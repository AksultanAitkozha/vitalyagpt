import requests
from bs4 import BeautifulSoup
import json
import re
import urllib.parse


BASE_URL = "http://ethresear.ch/"
CHUNK_SIZE = 200


def get_essay_urls():
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all <a> tags\*
    for link in soup.find_all("a"):
        href = link.get("href")
        if href:
            # Use urljoin to handle relative links
            full_url = urllib.parse.urljoin(url, href)
            # Avoid looping infinitely over the same pages, only scrape pages under 'vitalik.ca' and not under 'categories'
            if "vitalik.ca" in full_url and 'categories' not in full_url:
                # get the text from this page
                scrape_page(full_url)

    link_objects = []
    for link in links:
        url = link.get("href")
        if url and url.endswith(".html"):
            title = link.text
            link_objects.append({
                "url": url,
                "title": title
            })

    return link_objects


def get_essay_text_and_chunk(link_obj):
    title = link_obj['title']
    url = link_obj['url']

    full_url = BASE_URL + url
    response = requests.get(full_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    text = soup.find_all('table')[1].text

    cleaned_text = re.sub(r'\s+', ' ', text)
    cleaned_text = re.sub(r'\.([a-zA-Z])', '. \\1', cleaned_text)

    date = re.search(r'([A-Z][a-z]+ [0-9]{4})', cleaned_text)
    date_str = ""
    text_without_date = ""

    if date:
        date_str = date.group(0)
        text_without_date = cleaned_text.replace(date_str, "")
    else:
        text_without_date = cleaned_text

    essay_text = text_without_date.replace('\n', ' ')
    thanks_to = ""

    split_text = [s for s in essay_text.split(". ") if s]
    last_sentence = split_text[-1]

    if last_sentence and "Thanks to" in last_sentence:
        thanks_to_split = last_sentence.split("Thanks to")

        if thanks_to_split[1].strip()[-1] == ".":
            thanks_to = "Thanks to " + thanks_to_split[1].strip()
        else:
            thanks_to = "Thanks to " + thanks_to_split[1].strip() + "."

        essay_text = essay_text.replace(thanks_to, "")

    trimmed_content = essay_text.strip()
    length = len(trimmed_content)
    tokens = len(trimmed_content.split())

    chunks = []
    for i in range(0, length, CHUNK_SIZE):
        chunk = trimmed_content[i:i+CHUNK_SIZE]
        chunks.append({
            'essay_title': title,
            'essay_url': full_url,
            'essay_date': date_str,
            'essay_thanks': thanks_to.strip(),
            'content': chunk,
            'content_length': len(chunk),
            'content_tokens': len(chunk.split()),
            'embedding': []
        })

    essay = {
        "title": title,
        "url": full_url,
        "date": date_str,
        "thanks": thanks_to.strip(),
        "content": trimmed_content,
        "length": length,
        "tokens": tokens,
        "chunks": chunks
    }

    return essay


def get_and_chunk_all_essays():
    urls = get_essay_urls()
    all_essays = []

    for url in urls:
        essay = get_essay_text_and_chunk(url)
        all_essays.append(essay)

    return all_essays


all_essays = get_and_chunk_all_essays()


with open('pg.json', 'w') as f:
    json.dump(all_essays, f)
