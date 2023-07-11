import requests
from bs4 import BeautifulSoup
import urllib.parse
import string

CHUNK_SIZE = 200


# start from the main page
start_url = "https://vitalik.ca/"


def scrape(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all <a> tags
    for link in soup.find_all("a"):
        href = link.get("href")
        if href:
            # Use urljoin to handle relative links
            full_url = urllib.parse.urljoin(url, href)
            # Avoid looping infinitely over the same pages, only scrape pages under 'vitalik.ca' and not under 'categories'
            if "vitalik.ca" in full_url and 'categories' not in full_url:
                # get the text from this page
                scrape_page(full_url)


def scrape_page(url):
    print(f"Scraping: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text(strip=True)
    printable_text = ''.join(filter(lambda x: x in string.printable, text))

    # get and print the text only
    print(printable_text)


# Start the scraping process
scrape(start_url)
