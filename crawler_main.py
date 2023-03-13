import time
import os
from queue import Queue
import threading
import requests
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import traceback
import bs4

from backend.sql_commands import DBManager


# TODO: Add site domains for each seed into DB


# GLOBALS
USERAGENT = "fri-wier-GROUP_NAME"
frontier = Queue()      # urls to be visited
crawled_urls = set()    # urls that have been visited
domain_rules = {}       # robots.txt rules per visited domain
domain_ips = {}         # domain to ip address map
ip_last_visits = {}     # time of last visit per ip (to restrict request rate)
# list of domains we want to visit
visit_domains = ["https://gov.si", "https://evem.gov.si", "https://e-uprava.gov.si", "https://e-prostor.gov.si"]


def get_url_from_frontier():
    url = frontier.get()
    return url


def add_to_frontier(url):
    # Checks if url has already been crawled
    if url not in crawled_urls:
        # Checks if url fits into our domain constraints
        for domain in visit_domains:
            if domain in url:
                frontier.put(url)


def add_to_crawled_urls(url):
    crawled_urls.add(url)


def request_page(url):
    """Fetches page at url and returns HTML content and metadata as dict."""

    domain = urlparse(url).netloc
    site_data = None    # Parsed SITE metadata
    page_raw = None     # Raw PAGE content and metadata

    # If not enough time has elapsed since last request, return url to end of queue
    if domain in domain_ips:
        ip = domain_ips[domain]
        since_last_req = time.time() - ip_last_visits[ip]
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
        robots_content = requests.get(robots_url).text
        sitemap_urls = rp.site_maps()
        if sitemap_urls is None:
            sitemap_content = None
        else:
            sitemap_content = requests.get(sitemap_urls[0]).text
        site_data = {
            "domain": domain,
            "robots": robots_content,
            "sitemap": sitemap_content
        }

    # If URL is dissalowed by robots.txt, don't fetch
    if not domain_rules[domain].can_fetch(USERAGENT, url):
        return None, site_data

    # Make a GET request
    print("Fetching ", url)
    req_time = time.time()
    response = requests.get(url, stream=True)

    # Save server IP and request time
    if response.raw._connection.sock: # HACK
        ip = response.raw._connection.sock.getsockname()
        if domain not in domain_ips:
            domain_ips[domain] = ip
        ip_last_visits[ip] = req_time

    # Make raw page content and info dict 
    if response.ok and response.content:
        # Push url to crawled list
        add_to_crawled_urls(url)

        # TODO: Set HTML, BINARY or DUPLICATE but default can be HTML
        page_raw = {
            "html_content": response.text,
            "page_type_code": "HTML",
            "domain": domain,
            "url": url,
            "http_status_code": 200,
            "accessed_time": req_time
        }

    # TODO: Perform Selenium parsing if we suspect dynamic content.

    return page_raw, site_data


def parse_page(page_raw, base_url):
    """Parses HTML content and extract links (urls)."""

    # TODO: Detect duplicate pages based on content or hash.

    # TODO: If URL already parsed we must still add the link connection to DB.

    if page_raw is None:
        return None

    # Parse HTML and extract links
    soup = bs4.BeautifulSoup(page_raw["html_content"], 'html.parser')

    # Basic page info
    page_info = page_raw

    # Find the urls in page
    links = []
    for link in soup.select('a'):
        found_link = link.get('href')
        to = urljoin(base_url, found_link)
        links.append({"from_page": base_url, "to_page": to})

    # Find the images in page (<img> tags)
    images = []
    for img in soup.select('img'):
        found_src = img.get('src')
        if found_src is not None:
            src_full = urljoin(base_url, found_src)
            img_info = {
                "page_url": base_url,
                "filename": os.path.basename(src_full),
                "content_type": None, # TODO: ?
                "data": None,
                "accessed_time": None
            }
            images.append(img_info)

    # TODO: Page data?

    # TODO: Also include links from onclick events

    page_obj = {
        "info": page_info,
        "urls": links,
        "imgs": images
    }

    return page_obj


def save_to_db(page_obj, site_data, conn):
    """Saves parsed site and page data to DB."""

    if site_data is not None:
        DBManager.insert_site(conn, site_data)

    if page_obj is not None:
        # Add found urls to frontier (TODO: should this be here?)
        for url in page_obj["urls"]:
            add_to_frontier(url["to_page"])
        DBManager.insert_all(conn, page_obj['info'], page_obj['urls'], page_obj['imgs'])


class Crawler(threading.Thread):
    """A single web crawler instance - continuously runs in own thread."""

    def __init__(self, thread_id, frontier_in, conn):
        super().__init__()
        self.threadID = thread_id
        self.frontier = frontier_in
        self.conn = conn
        self.daemon = True

    def process_next(self):
        """Fetches, parses and saves next page from frontier."""

        url = get_url_from_frontier()
        page_raw, site_data = request_page(url)
        page_obj = parse_page(page_raw, url)
        save_to_db(page_obj, site_data, self.conn)

    def run(self):
        """Continuously processes pages from frontier."""

        while True:
            try:
                self.process_next()
            except Exception as e:
                print(traceback.format_exc())
                # TODO


if __name__ == '__main__':

    # Add seed urls of domains we want to visit
    for domain_url in visit_domains:
        add_to_frontier(domain_url)

    # Init base domains
    for page_url in frontier.queue:
        domain_rules[page_url] = None

    NTHREADS = 1

    db_manager = DBManager()

    crawlers = []
    for i in range(NTHREADS):
        crawler = Crawler(i, frontier, db_manager.get_connection())
        crawlers.append(crawler)
        crawler.start()

    while True:
        time.sleep(1)
        # try:
        #     time.sleep(1)
        # except Exception as e:
        #     print(e)
        #     print(frontier)
        #     print(ip_last_visits)
        #     exit()
