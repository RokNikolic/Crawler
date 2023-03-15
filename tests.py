from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# Options for the browser
option = webdriver.ChromeOptions()
option.add_argument('--headless')

# Get and create the browser object
service = Service(r'\web_driver\chromedriver.exe')
browser = webdriver.Chrome(service=service, options=option)

browser.get('https://www.imdb.com/chart/top/')  # Getting page HTML through request
soup = BeautifulSoup(browser.page_source, 'html.parser')  # Parsing content using beautifulsoup. Notice driver.page_source instead of page.content

links = soup.select("table tbody tr td.titleColumn a")  # Selecting all of the anchors with titles
first10 = links[:10]  # Keep only the first 10 anchors
for anchor in first10:
    print(anchor.text)  # Display the innerText of each anchor
