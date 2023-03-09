import requests
import bs4
from urllib.parse import urljoin

frontier = []
crawled_urls = set()

def get_frontier_url():
    task = frontier[0]
    frontier.pop(0)
    return task

def add_to_frontier(url):
    if not url in crawled_urls:
        frontier.append(url)


class Crawler:
    def __init__(self, frontier) -> None:
        self.frontier = frontier
        
    @staticmethod
    def request(url: str):
        # Making a GET request
        responce = requests.get(url)
        
        # check status code for 200
        if responce.ok:
            return responce.text
        else:
            return None

    @staticmethod
    def parse(page, parsed_url):
        # Parse HTML and extract links
        soup = bs4.BeautifulSoup(page, 'html.parser')
        
        # Array for found links
        links = []
        # Find 'a' tag
        for link in soup.select('a'):
            # Find 'href' tag
            found_link = link.get('href')
            # Combine found links and combine with base path to make absolute path
            links.append(urljoin(parsed_url, found_link))

        return links

    def worker(self):
        pass

    def run(self):
        pass




if __name__ == '__main__':
    print('Crawlin time')

    crawler = Crawler(frontier)

    url = 'https://en.wikipedia.org/wiki/Main_Page'
    response = Crawler.request(url)

    print(Crawler.parse(response, url))
