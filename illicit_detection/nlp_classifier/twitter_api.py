# fetch_text.py

import requests
from bs4 import BeautifulSoup
from newspaper import Article
from requests_html import HTMLSession


def fetch_text_from_url(url):
    """
    Fetch and extract readable text from any webpage (including JS-rendered).
    Automatically handles fallbacks if one method fails.
    """
    # 1️⃣ Try newspaper3k (best for news/article content)
    try:
        article = Article(url)
        article.download()
        article.parse()
        if article.text.strip():
            return article.text
    except Exception:
        pass

    # 2️⃣ Try BeautifulSoup with requests (fast for static pages)
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove unwanted tags
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()

        text = " ".join(soup.get_text().split())
        if text.strip():
            print(text)
            return text
    except Exception:
        pass

    # 3️⃣ Try rendering JavaScript content using requests_html
    try:
        session = HTMLSession()
        response = session.get(url)
        response.html.render(timeout=30, sleep=2)
        text = " ".join(response.html.text.split())
        if text.strip():
            print(text)
            return text
    except Exception:
        pass

    # If all fail
    return "Failed to extract text from the given URL."
