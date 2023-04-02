import datetime
import re
import socket
import time
import os
import threading
import requests
import hashlib
from queue import Queue
import logging
import dill
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from backend.sql_commands import DBManager


# TODO: Add site domains for each seed into DB


# GLOBALS
USERAGENT = "fri-wier-GROUP_NAME"
headers = {'User-Agent': USERAGENT}

frontier = Queue()      # urls to be visited
crawled_urls = set()    # urls that have been visited
domain_rules = {}       # robots.txt rules per visited domain
domain_ips = {}         # domain to ip address map
ip_last_visits = {}     # time of last visit per ip (to restrict request rate)
selenium_count = 0
bad_response_count = 0

# list of domains we want to visit
visit_domains = ["https://gov.si", "https://evem.gov.si", "https://e-uprava.gov.si", "https://e-prostor.gov.si"]

# Options for the selenium browser
option = webdriver.ChromeOptions()
option.add_argument('--headless')

# Logger setup
crawl_logger = logging.getLogger('crawler_logger')

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('main_log.log')
file_handler.setLevel(logging.WARNING)
error_handler = logging.FileHandler('error_log.log')
error_handler.setLevel(logging.ERROR)

formatter1 = logging.Formatter('%(asctime)s - %(message)s')
stream_handler.setFormatter(formatter1)
file_handler.setFormatter(formatter1)
error_handler.setFormatter(formatter1)

crawl_logger.addHandler(stream_handler)
crawl_logger.addHandler(file_handler)


def format_page_data(header):
    if "pdf" in header:
        return "PDF"
    elif "doc" in header:
        return "DOC"
    elif "docx" in header:
        return "DOCX"
    elif "ppt" in header:
        return "PPT"
    elif "pptx" in header:
        return "PPTX"
    else:
        # Regex to extract just the file type from Content-Type header
        return re.search(r"/(.*)", header).group(1).upper()


def get_hash(page_content):
    """Returns hash from the given HTML content."""
    encoded_content = page_content.encode('utf-8')
    hashcode = hashlib.sha256(encoded_content).hexdigest()
    return hashcode


def check_duplicate(conn, page_content, url):
    """Check if page is a duplicate of another."""
    page_hash = get_hash(page_content)
    t = DBManager.check_if_page_exists(conn, page_hash, url)
    return t


def get_url_from_frontier():
    url = frontier.get()
    return url


def add_urls_to_frontier(links):
    for link in links:
        add_to_frontier(link['to_page'])


def add_to_frontier(url):
    # Removes query elements and anchor elements from url
    clean_url = re.sub(r"/*([?#].*)?$", "", url)
    if clean_url not in crawled_urls:
        # Checks if url fits into our domain constraints
        for domain in visit_domains:
            if domain in clean_url:
                frontier.put(clean_url)
                return True
    return False


def request_page(url):
    """Fetches page at url and returns HTML content and metadata as dict."""

    domain = urlparse(url).netloc
    site_data = None    # Parsed SITE metadata
    page_raw = {
        "html_content": "",
        "hashcode": "",
        "page_type_code": "HTML",
        "domain": domain,
        "url": url,
        "http_status_code": 0,
        "accessed_time": 0,
        "page_data": {},            # if page is BINARY, page_data contains metadata
        "duplicate_url": "",        # If page is duplicate, url of original page
    }
    global selenium_count
    global bad_response_count

    # If not enough time has elapsed since last request, return url to end of queue
    if domain in domain_ips:
        ip = domain_ips[domain]
        since_last_req = time.perf_counter() - ip_last_visits[ip]
        robots_delay = domain_rules[domain].crawl_delay(USERAGENT)
        min_delay = robots_delay if robots_delay is not None else 5
        if since_last_req < min_delay:
            add_to_frontier(url)
            return None, None

    else:
        # Save robots.txt rules for new domain
        rp = RobotFileParser()
        robots_url = urljoin(url, domain) + "/robots.txt"
        rp.set_url(robots_url)
        rp.read()
        domain_rules[domain] = rp

        # Make site info dict with robots.txt and sitemap contents
        robots_content = requests.get(robots_url, headers).text
        sitemap_urls = rp.site_maps()
        if sitemap_urls is None:
            sitemap_content = None
        else:
            sitemap_content = requests.get(sitemap_urls[0], headers).text
        site_data = {
            "domain": domain,
            "robots": robots_content,
            "sitemap": sitemap_content
        }

    # If URL is disallowed by robots.txt, don't fetch
    if not domain_rules[domain].can_fetch(USERAGENT, url):
        return None, site_data

    # # If URL does not contain gov.si don't fetch
    if "gov.si" not in url:
        return None, site_data

    # Make a GET request
    crawl_logger.info(f"Fetching {url}")
    req_time = time.perf_counter()
    response = requests.get(url, headers, stream=True)

    # Save server IP and request time
    if socket.gethostbyname(domain):
        ip = socket.gethostbyname(domain)
        if domain not in domain_ips:
            domain_ips[domain] = ip
        ip_last_visits[ip] = req_time

    page_raw["accessed_time"] = req_time
    page_raw["http_status_code"] = response.status_code

    # Check if we got redirected and if we already crawled the redirect url
    if response.history and response.url != url and response.url in crawled_urls:
        if response.url in crawled_urls:
            # crawl_logger.info("Already crawled redirect url")
            page_raw["page_type_code"] = "DUPLICATE"
            page_raw["duplicate_url"] = response.url
    elif response.ok and response.content and "text/html" in response.headers["content-type"]:
        page_raw['html_content'] = response.text
        # Check if we need to use selenium
        if len(response.text) < 30000:
            crawl_logger.warning(f"Using selenium, use count: {selenium_count}")
            # Use selenium
            selenium_response = request_with_selenium(url)
            page_raw['html_content'] = selenium_response
            selenium_count += 1  # Count selenium uses
        page_raw["page_type_code"] = "HTML"
        page_raw["hashcode"] = get_hash(page_raw["html_content"])
        crawled_urls.add(re.sub(r"/*([?#].*)?$", "", url))
        crawl_logger.warning(f"Amount of crawled urls: {len(crawled_urls)}")
    elif response.ok and response.content:
        page_raw["page_type_code"] = "BINARY"
        page_raw["page_data"] = {
            "data_type_code": format_page_data(response.headers["content-type"]),
            "data": None
        }
        crawled_urls.add(re.sub(r"/*([?#].*)?$", "", url))
    else:
        bad_response_count += 1
        crawl_logger.warning(f"Response not ok, count: {bad_response_count}")

        # If response not ok, we must store a page_raw with only url and http_status_code
        page_raw["http_status_code"] = response.status_code
        page_raw["page_type_code"] = "HTML"
        return page_raw, site_data

    return page_raw, site_data


def parse_page(page_raw, base_url, conn):
    """Parses HTML content and extract links (urls)."""

    page_obj = {
        "info": page_raw,
        "urls": [],
        "imgs": []
    }

    if page_raw is None:
        return None

    duplicate_url = check_duplicate(conn, page_raw['html_content'], page_raw['url'])
    if page_raw['page_type_code'] == 'DUPLICATE' or duplicate_url:
        page_obj['info']['page_type_code'] = 'DUPLICATE'
        page_obj['info']['duplicate_url'] = duplicate_url
        page_obj['info']['hashcode'] = None
        page_obj['info']['html_content'] = None
        return page_obj

    # Parse HTML and extract links
    soup = BeautifulSoup(page_raw["html_content"], 'html.parser')

    # Find the urls in page
    for link in soup.select('a'):
        found_link = link.get('href')
        to = urljoin(base_url, found_link)
        clean_to = re.sub(r"/*([?#].*)?$", "", to)
        page_obj['urls'].append({"from_page": base_url, "to_page": clean_to})

    # Find the images in page (<img> tags)
    for img in soup.select('img'):
        found_src = img.get('src')
        if found_src is not None:
            src_full = urljoin(base_url, found_src)

            # Check if src_full is data:image
            if re.match(r"data:image", src_full):
                content_type = re.match(r"(data:image/.*;.*),", src_full).group(1)
                src_full = "BINARY DATA"
            elif len(src_full) >= 255:
                # If src is too long, don't save it
                content_type = ""
                src_full = "BINARY DATA"
            else:
                content_type = os.path.splitext(src_full)[1]

            img_info = {
                "filename": src_full,
                "content_type": content_type,
                "data": None,
                "accessed_time": page_raw["accessed_time"]
            }
            page_obj["imgs"].append(img_info)

    # Find the tags with onclick attribute using BeautifulSoup
    for tag in soup.find_all(onclick=True):
        found_link = tag.get('onclick')
        if found_link is not None:
            # Find the url in the onclick attribute
            valid_links = re.findall(r"(?i)\b(?:(?:https?|ftp)://|www\.|/)\S+\b", found_link)
            for link in valid_links:
                if link is not None:
                    found_link = link
                    to = urljoin(base_url, found_link)
                    clean_to = re.sub(r"/*([?#].*)?$", "", to)
                    page_obj['urls'].append({"from_page": base_url, "to_page": clean_to})
                    # crawl_logger.info(f"Found link in onclick attribute: {clean_to}")

    return page_obj


def request_with_selenium(url):
    """Loads a page with a full web browser to parse javascript"""

    # Get and create the selenium browser object
    service = Service(r'\web_driver\chromedriver.exe')
    browser = webdriver.Chrome(service=service, options=option)

    # Crawler should wait for 5 seconds before requesting the page again
    time.sleep(5)

    browser.get(url)
    page = browser.page_source
    return page


def save_to_db(page_obj, site_data, conn, thread_id):
    """Saves parsed site and page data to DB."""

    if site_data is not None:
        DBManager.insert_site(conn, site_data)

    if page_obj is not None:
        if page_obj['info']['page_type_code'] != 'DUPLICATE':
            add_urls_to_frontier(page_obj['urls'])
        DBManager.insert_all(conn, page_obj['info'], page_obj['urls'], page_obj['imgs'])
        crawl_logger.info(f"Thread:{thread_id} Processed: {page_obj['info']['url']}")


class Crawler(threading.Thread):
    """A single web crawler instance - continuously runs in own thread."""

    def __init__(self, thread_id, frontier_in, conn, stop_event):
        super().__init__()
        self.threadID = thread_id
        self.frontier = frontier_in
        self.conn = conn
        self.daemon = True
        self.stop_event = stop_event

    def process_next(self):
        """Fetches, parses and saves next page from frontier."""

        url = get_url_from_frontier()
        page_raw, site_data = request_page(url)
        page_obj = parse_page(page_raw, url, self.conn)
        save_to_db(page_obj, site_data, self.conn, self.threadID)

    def run(self):
        """Continuously processes pages from frontier."""

        while not self.stop_event.is_set():
            try:
                self.process_next()
            except Exception as er:
                crawl_logger.exception(f"Error: {er}")
                continue


if __name__ == '__main__':
    crawl_logger.warning(f"Start Time: {datetime.datetime.now()}")

    try:
        # If it exists, start from a checkpoint frontier
        if os.path.exists("checkpoint.pkl"):
            with open("checkpoint.pkl", "rb") as f:
                frontier, crawled_urls = dill.load(f)
            crawl_logger.warning("Loading frontier!")
    except Exception as e:
        crawl_logger.exception(f"Error: {e}")

    # Add seed urls of domains we want to visit if frontier is empty
    if frontier.empty():
        crawl_logger.warning("Starting from empty frontier!")
        for domain_url in visit_domains:
            add_to_frontier(domain_url)

    # Init base domains
    for page_url in frontier.queue:
        domain_rules[page_url] = None

    NTHREADS = 10  # Use 10
    # Testing different thread amounts for 15 minutes of crawling
    # 1: Amount of crawled urls: 335
    # 2: Amount of crawled urls: 621
    # 4: Amount of crawled urls: 1067
    # 6: Amount of crawled urls: 1261
    # 8: Amount of crawled urls: 1406
    # 10: Amount of crawled urls: 1702
    # 12: Amount of crawled urls: 1640
    # 10: Amount of crawled urls: 1579, Using selenium, use count: 37, len < 20.000
    # 10: Amount of crawled urls: 1266, Using selenium, use count: 383, len < 30.000  <<< good options

    db_manager = DBManager()

    crawlers = []
    event = threading.Event()
    for i in range(NTHREADS):
        crawler = Crawler(i, frontier, db_manager.get_connection(), event)
        crawlers.append(crawler)
        crawler.start()

    # Run crawlers for a set time
    time_start = time.perf_counter()
    time_dif = time_start - time.perf_counter()

    run_time = (3*60)  # In minutes
    while time_dif < (run_time * 60):
        time.sleep(1)
        time_dif = time.perf_counter() - time_start

    # Stopping the threads with event setting
    event.set()

    # Store variables frontier and crawled_urls
    with open('checkpoint.pkl', 'wb') as f:
        dill.dump([frontier, crawled_urls], f)

    crawl_logger.warning(f"Using selenium, use count: {selenium_count}")
