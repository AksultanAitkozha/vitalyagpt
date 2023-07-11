import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import json


BASE_URL = "https://vitalik.ca/"
CHUNK_SIZE = 200  # Define your preferred chunk size


def get_essay_text_and_chunk(title, url):
    full_url = urllib.parse.urljoin(BASE_URL, url)
    response = requests.get(full_url)
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(strip=True)

    # For date, try to find a pattern like "Month Year" at the start of the text
    date_match = re.search(r"^[A-Z][a-z]+\s\d{4}", text)
    date = date_match.group(0) if date_match else ""

    # For thanks, it's more difficult as there's no standard phrase across articles.
    # You may need to come up with a more sophisticated approach. Here's a simple one:
    thanks_match = re.search(r"Thanks to .*\.", text)
    thanks = thanks_match.group(0) if thanks_match else ""

    cleaned_text = re.sub(r"\s+", " ", text)
    length = len(cleaned_text)
    tokens = len(cleaned_text.split())
    chunks = [
        cleaned_text[i : i + CHUNK_SIZE]
        for i in range(0, len(cleaned_text), CHUNK_SIZE)
    ]

    essay = {
        "title": title,
        "url": full_url,
        "date": date,
        "thanks": thanks,
        "content": cleaned_text,
        "length": length,
        "tokens": tokens,
        "chunks": chunks,
    }

    return essay


def get_and_chunk_all_essays():
    start_url = BASE_URL
    response = requests.get(start_url)
    soup = BeautifulSoup(response.text, "html.parser")

    all_essays = []

    # Find all <a> tags
    for link in soup.find_all("a"):
        href = link.get("href")
        if href and "categories" not in href:
            # Full URL for the essay
            full_url = urllib.parse.urljoin(start_url, href)
            essay = get_essay_text_and_chunk(link.text, full_url)
            all_essays.append(essay)

    return all_essays


all_essays = get_and_chunk_all_essays()


def chunk_content(content):
    # Return an empty list if content is None
    if content is None:
        return []

    # Splitting the content into sentences
    split = content.split(". ")
    chunk_text = ""

    essay_text_chunks = []

    for sentence in split:
        # If adding a new sentence exceeds the CHUNK_SIZE or token limit, store the current chunk_text
        if (
            len(chunk_text + sentence) > CHUNK_SIZE
            or len((chunk_text + sentence).split()) > 200
        ):
            essay_text_chunks.append(chunk_text)
            chunk_text = ""

        chunk_text += sentence + ". "

    # Adding the last chunk
    essay_text_chunks.append(chunk_text.strip())

    return essay_text_chunks


def create_chunks(title, url, date, thanks, essay_text_chunks):
    # Create chunks for each essay
    essay_chunks = []
    for text in essay_text_chunks:
        trimmed_text = text.strip()

        chunk = {
            "essay_title": title,
            "essay_url": url,
            "essay_date": date,
            "essay_thanks": thanks,
            "content": trimmed_text,
            "content_length": len(trimmed_text),
            "content_tokens": len(trimmed_text.split()),
            "embedding": [],
        }

        essay_chunks.append(chunk)

    # Merge chunks if their token size is less than 100
    if len(essay_chunks) > 1:
        i = 0
        while i < len(essay_chunks):
            chunk = essay_chunks[i]
            if chunk["content_tokens"] < 100 and i > 0:
                prev_chunk = essay_chunks[i - 1]
                prev_chunk["content"] += " " + chunk["content"]
                prev_chunk["content_length"] += chunk["content_length"]
                prev_chunk["content_tokens"] += chunk["content_tokens"]
                essay_chunks.pop(i)
            else:
                i += 1

    return essay_chunks


def create_essay_object(essay_data, chunks):
    essay = {
        "title": essay_data["title"],
        "url": essay_data["url"],
        "date": essay_data["date"],
        "thanks": essay_data["thanks"],
        "content": essay_data["content"],
        "length": len(essay_data["content"]),
        "tokens": len(essay_data["content"].split()),
        "chunks": chunks,
    }
    return essay


def create_json(essays):
    json_content = {
        "current_date": "2023-07-05",
        "author": "Vitalik Buterin",
        "url": BASE_URL,
        "length": sum(essay["length"] for essay in essays),
        "tokens": sum(essay["tokens"] for essay in essays),
        "essays": essays,
    }
    return json_content


def main():
    # Get your essays data
    essays_data = get_and_chunk_all_essays()

    essays = []
    for essay_data in essays_data:
        # Chunking the content
        essay_text_chunks = chunk_content(essay_data["content"])

        # Creating chunks
        chunks = create_chunks(
            essay_data["title"],
            essay_data["url"],
            essay_data["date"],
            essay_data["thanks"],
            essay_text_chunks,
        )

        # Creating essay object
        essay = create_essay_object(essay_data, chunks)

        # Adding essay to essays
        essays.append(essay)

    # Create final JSON object
    json_content = create_json(essays)

    with open("scripts/pg.json", "w", encoding="utf-8") as f:
        json.dump(json_content, f, ensure_ascii=False)


# Run the main function
if __name__ == "__main__":
    main()
