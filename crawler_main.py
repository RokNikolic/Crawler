import asyncio
import html.parser


class UrlParser(html.parser.HTMLParser):
    def __init__(self, base: str,):
        super().__init__()
        self.base = base
        self.links = set()

    def handle_starttag(self, tag: str, attrs):
        # look for <a href="...">
        if tag != "a":
            return

        for attr, url in attrs:
            if attr != "href":
                continue

            #if (url := self.filter_url(self.base, url)) is not None:
            else:
                self.links.add(url)

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
        

    def worker(self):
        while True:
            try:
                self.process_one()
            except asyncio.CancelledError:
                return

    def parse(self, url):
        pass

    def crawl(self):
        pass






if __name__ == '__main__':
    print('Crawlin time')
