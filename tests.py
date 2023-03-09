import asyncio
import bs4
import requests
from urllib.parse import urljoin

def request(url: str):
    # Making a GET request
    responce = requests.get(url)
    
    # check status code for 200
    if responce.ok:
        return responce.content
    else:
        # print(responce)
        return None

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

url = 'https://en.wikipedia.org/wiki/Main_Page'
response = request(url)

print(parse(response, url))










async def print1(string: str):
    print(string)
    await asyncio.sleep(0.5)
    print("Done")


async def main():
    todo = ['get 1', 'get 2', 'get 3']

    tasks = [asyncio.create_task(print1(item)) for item in todo]

    done, pending = await asyncio.wait(tasks)


if __name__ == '__main__':
    #asyncio.run(main())
    pass
