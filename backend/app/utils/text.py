# d:\Project\ContestMind\backend\app\utils\text.py
from bs4 import BeautifulSoup


def clean_html(html_content: str) -> str:
    """
    Removes HTML tags from a string.
    """
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text()
