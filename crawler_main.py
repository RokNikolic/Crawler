import time
import os
from queue import Queue
import threading
import requests
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

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


def get_url_from_frontier():
    url = frontier.get()
    crawled_urls.add(url) # TODO: Do this on successful request instead?
    return url


def add_to_frontier(url):
    if not url in crawled_urls:
        frontier.put(url)


def request(url):
    """Fetches page at url and returns HTML content."""

    # TODO: Don't request if outside given domains?

    # TODO: Add correct sitemap handling based on the current domain.

    domain = urlparse(url).netloc

    # If not enough time has elapsed since last request, return url to end of queue
    if domain in domain_ips:
        ip = domain_ips[domain]
        since_last_req = time.time() - ip_last_visits[ip]

        robots_delay = domain_rules[domain].crawl_delay(USERAGENT)
        min_delay = robots_delay if robots_delay is not None else 5
        if since_last_req < min_delay:
            add_to_frontier(url)
            return None
    else:
        # Save robots.txt rules for new domain
        rp = RobotFileParser()
        rp.set_url(urljoin(url, domain) + "/robots.txt")
        rp.read()
        domain_rules[domain] = rp

    if not domain_rules[domain].can_fetch(USERAGENT, url):
        return
        
    # Make a GET request
    print("Fetching ", url)
    req_time = time.time()
    response = requests.get(url, stream=True)

    # Save server IP and request time
    ip = response.raw._connection.sock.getsockname()
    if domain not in domain_ips:
        domain_ips[domain] = ip
    ip_last_visits[ip] = req_time

    # Check response validity
    if response.ok and len(response.content) > 0:
        return response.text
    else:
        return None

    # TODO: Perform Selenium parsing if we suspect dynamic content.


def parse(html, base_url):
    """Parses HTML content and extract links (urls)."""

    # TODO: Detect duplicate pages based on content or hash.

    # TODO: If URL already parsed we must still add the link connection to DB.

    if html is None: return None

    # Parse HTML and extract links
    soup = bs4.BeautifulSoup(html, 'html.parser')

    # Find the urls in page
    links = []
    for link in soup.select('a'):
        found_link = link.get('href')
        links.append(urljoin(base_url, found_link))

    # TODO: Also include links from onclick events

    # TODO: Detect images based on img tag with src containing URL

    return links


def save(data, url, conn):
    """Saves parsed page content to DB."""

    if data is None: return

    for link in data:
        add_to_frontier(link)

    site_json = {"domain": url}
    DBManager.insert_site(conn, site_json)
    # THROWS: "robots" ?

    # TODO: insert parsed data 


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
        html = request(url)
        data = parse(html, url)
        save(data, url, self.conn)
        pass

    def run(self):
        """Continuously processes pages from frontier."""

        while True:
            try:
                self.process_next()
            except Exception as e:
                print(e)
                # TODO
                pass


if __name__ == '__main__':

    add_to_frontier("https://gov.si")
    add_to_frontier("https://evem.gov.si")
    add_to_frontier("https://e-uprava.gov.si")
    add_to_frontier("https://e-prostor.gov.si")

    # Init base domains
    for url in frontier.queue:
        domain_rules[url] = None

    NTHREADS = 2

    db_manager = DBManager()

    crawlers = []
    for i in range(NTHREADS):
        crawler = Crawler(i, frontier, db_manager.get_connection())
        crawlers.append(crawler)
        crawler.start()

    while True:
        try:
            time.sleep(1)
        except Exception as e:
            print(e)
            print(frontier)
            print(ip_last_visits)
            exit()
