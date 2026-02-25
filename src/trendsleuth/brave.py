"""Brave Search API client."""

import logging
import time
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


@dataclass
class BraveConfig:
    """Configuration for Brave Search API."""

    api_key: str
    rate_limit_rps: float = 1.0  # Requests per second


@dataclass
class SearchResult:
    """A single search result from Brave."""

    url: str
    title: str
    description: str


class BraveClient:
    """Client for Brave Search API with rate limiting."""

    BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, config: BraveConfig):
        """Initialize Brave client.

        Args:
            config: Brave API configuration
        """
        self.config = config
        self.last_request_time = 0
        self.min_interval = 1.0 / config.rate_limit_rps

        # Setup session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _rate_limit(self) -> None:
        """Enforce rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def search(
        self,
        query: str,
        count: int = 5,
        timeout: int = 10,
    ) -> list[SearchResult]:
        """Search using Brave API.

        Args:
            query: Search query string
            count: Number of results to return
            timeout: Request timeout in seconds

        Returns:
            List of search results
        """
        self._rate_limit()

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.config.api_key,
        }

        params = {
            "q": query,
            "count": count,
        }

        try:
            logger.debug(f"Searching Brave: {query}")
            response = self.session.get(
                self.BASE_URL,
                headers=headers,
                params=params,
                timeout=timeout,
            )
            response.raise_for_status()

            data = response.json()
            results = []

            # Extract web results
            web_results = data.get("web", {}).get("results", [])
            for item in web_results[:count]:
                results.append(
                    SearchResult(
                        url=item.get("url", ""),
                        title=item.get("title", ""),
                        description=item.get("description", ""),
                    )
                )

            logger.debug(f"Found {len(results)} results")
            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Brave search failed for query '{query}': {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during Brave search: {e}")
            return []
