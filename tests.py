import asyncio
import html.parser


async def print1(string: str):
    print(string)
    await asyncio.sleep(0.5)
    print("Done")


async def main():
    todo = ['get 1', 'get 2', 'get 3']

    tasks = [asyncio.create_task(print1(item)) for item in todo]

    done, pending = await asyncio.wait(tasks)


class UrlParser(html.parser.HTMLParser):
    def __init__(self, base: str,):
        super().__init__()
        self.base = base
        self.links = set()

    def handle_starttag(self, tag: str, attrs):
        # look for <a href="...">
        if tag != "a":
            return None

        for attr, url in attrs:
            if attr != "href":
                continue

            #if (url := self.filter_url(self.base, url)) is not None:
            else:
                self.links.add(url)


if __name__ == '__main__':
    #asyncio.run(main())
