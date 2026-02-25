"""Web scraping utilities for extracting text from URLs."""

import logging
import re
from typing import Optional
from html.parser import HTMLParser

import requests

logger = logging.getLogger(__name__)


class HTMLTextExtractor(HTMLParser):
    """Simple HTML parser to extract readable text."""
    
    # Tags to skip completely
    SKIP_TAGS = {'script', 'style', 'head', 'meta', 'link', 'noscript'}
    
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_level = 0
    
    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self.skip_level += 1
    
    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS:
            self.skip_level = max(0, self.skip_level - 1)
    
    def handle_data(self, data):
        if self.skip_level == 0:
            text = data.strip()
            if text:
                self.text_parts.append(text)
    
    def get_text(self) -> str:
        """Get extracted text."""
        return " ".join(self.text_parts)


def extract_text_from_html(html: str, max_length: int = 10000) -> str:
    """Extract readable text from HTML.
    
    Args:
        html: HTML content
        max_length: Maximum text length to extract
        
    Returns:
        Extracted text
    """
    try:
        parser = HTMLTextExtractor()
        parser.feed(html)
        text = parser.get_text()
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text[:max_length]
    except Exception as e:
        logger.warning(f"Failed to parse HTML: {e}")
        return ""


def fetch_page_text(
    url: str,
    timeout: int = 10,
    max_length: int = 10000,
) -> Optional[str]:
    """Fetch and extract text from a URL.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        max_length: Maximum text length to extract
        
    Returns:
        Extracted text or None if fetch failed
    """
    try:
        logger.debug(f"Fetching: {url}")
        
        headers = {
            "User-Agent": "TrendSleuth/1.0 (Research Bot)",
            "Accept": "text/html,application/xhtml+xml",
        }
        
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            allow_redirects=True,
        )
        response.raise_for_status()
        
        # Only process HTML content
        content_type = response.headers.get("Content-Type", "")
        if "html" not in content_type.lower():
            logger.debug(f"Skipping non-HTML content: {content_type}")
            return None
        
        text = extract_text_from_html(response.text, max_length)
        logger.debug(f"Extracted {len(text)} characters from {url}")
        
        return text if text else None
        
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Unexpected error fetching {url}: {e}")
        return None
