import requests
from urllib.parse import urljoin
import threading
import time

import bs4

import backend.sql_commands as backend


frontier = []
crawled_urls = set()

def get_frontier_url():
    url = frontier.pop(0)
    crawled_urls.add(url)
    return url

def add_to_frontier(url):
    if not url in crawled_urls:
        frontier.append(url)


def fetch(url):
    """Fetches page at url and returns HTML content."""

    response = requests.get(url)

    if response.ok:
        return response.text
    else:
        return None
    
def parse(page, base_url):
    """Parses HTML content and extract links (urls)."""

    if page is None: return None
    soup = bs4.BeautifulSoup(page, 'html.parser')

    links = []
    for link in soup.select('a'):
        found_link = link.get('href')
        links.append(urljoin(base_url, found_link))

    return links


def save(data, url, conn):
    """Saves parsed page content to DB."""

    for link in data:
        #print("Adding " + link + " to frontier...")
        add_to_frontier(link)

    site_json = {"domain": url}
    backend.insert_site(conn, site_json)

    # TODO: insert parsed data 



class Crawler(threading.Thread):
    """A single web crawler instance - continuously runs in own thread."""

    def __init__(self, threadID, frontier):
        super().__init__()
        self.threadID = threadID
        self.frontier = frontier
        self.daemon = True

    def process_next(self):
        """Fetches, parses and saves next page from frontier."""
        
        url = get_frontier_url()
        html = fetch(url)
        data = parse(html, url)
        save(data, url, self.conn)
        pass

    def run(self):
        """Continuously processes pages from frontier."""

        self.conn = backend.get_connection()
        #self.conn = None

        while(True):
            try:
                self.process_next()
            except Exception as e:
                # TODO
                pass




if __name__ == '__main__':

    url = 'https://en.wikipedia.org/wiki/Main_Page'
    add_to_frontier(url)

    NTHREADS = 3

    crawlers = []
    for i in range(NTHREADS):
        crawler = Crawler(i, frontier)
        crawlers.append(crawler)
        crawler.start()

    while(True):
        try:
            time.sleep(1)
        except:
            print(frontier)
            exit()
