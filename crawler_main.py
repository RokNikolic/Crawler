import queue

import requests
from urllib.parse import urljoin
import threading
import time
import bs4
from queue import Queue
from backend import DBManager

# TODO: Initial seed is gov.si, evem.gov.si, e-uprava.gov.si and e-prostor.gov.si
# TODO: Add site domains for each seed into DB


frontier = Queue()
crawled_urls = set()


def get_url_from_frontier():
    url = frontier.get()
    crawled_urls.add(url)
    return url


def add_to_frontier(url):
    if not url in crawled_urls:
        frontier.put(url)


def request(url):
    """Fetches page at url and returns HTML content."""

    # TODO: Add correct robots.txt handling based on the current domain.
    # Our User-Agent = fri-wier-GROUP_NAME

    # TODO: Add correct sitemap handling based on the current domain.

    # TODO: Requests of all crawlers must be sent with 5 second delays (not only to one domain but also IP)

    # Make a GET request
    response = requests.get(url)

    # Check status code for 200
    if response.ok:
        # TODO: Account for cases when status code OK but empty or incorrect page returned (example 404 page)
        return response.text
    else:
        return None

    # TODO: Perform Selenium parsing if we suspect dynamic content.


def parse(page, base_url):
    """Parses HTML content and extract links (urls)."""

    # TODO: Detect duplicate pages based on content or hash.

    # TODO: If URL already parsed we must still add the link connection to DB.

    if page is None:
        return None
    # Parse HTML and extract links
    soup = bs4.BeautifulSoup(page, 'html.parser')

    links = []
    # Find the 'a' tag
    for link in soup.select('a'):
        # Find the 'href' tag
        found_link = link.get('href')
        # Combine found links and base path
        links.append(urljoin(base_url, found_link))

    # TODO: Also include links from onclick events

    # TODO: Detect images based on img tag with src containing URL

    return links


def save(data, url, conn):
    """Saves parsed page content to DB."""

    for link in data:
        # print("Adding " + link + " to frontier...")
        add_to_frontier(link)

    site_json = {"domain": url}
    DBManager.insert_site(conn, site_json)

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

    test_url = 'https://en.wikipedia.org/wiki/Main_Page'
    add_to_frontier(test_url)

    NTHREADS = 3

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
            exit()
