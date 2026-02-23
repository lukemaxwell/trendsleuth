"""Reddit API client using PRAW for synchronous operations."""

import time
import signal
from typing import Optional

import praw
from praw.models import Submission, Comment
from praw.exceptions import RedditAPIException, PRAWException
from prawcore.exceptions import PrawcoreException

from trendsleuth.config import RedditConfig


class TimeoutError(Exception):
    """Exception raised when a Reddit API call times out."""
    pass


def _timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Reddit API call timed out")


class RedditClient:
    """Client for interacting with Reddit API."""
    
    def __init__(self, config: RedditConfig, timeout: int = 30):
        """Initialize the Reddit client.
        
        Args:
            config: Reddit configuration object
            timeout: Default timeout in seconds for API calls
        """
        self.config = config
        self.timeout = timeout
        self._client: Optional[praw.Reddit] = None
    
    @property
    def client(self) -> praw.Reddit:
        """Get or create the Reddit client instance."""
        if self._client is None:
            self._client = praw.Reddit(
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
                user_agent=self.config.user_agent,
                check_for_updates=False,
                comment_sort="top",
            )
        return self._client
    
    def _with_timeout(self, func, *args, timeout=None, **kwargs):
        """Execute a function with a timeout.
        
        Args:
            func: Function to execute
            *args: Positional arguments to pass
            timeout: Timeout in seconds (uses default if not specified)
            **kwargs: Keyword arguments to pass
            
        Returns:
            Result of the function
            
        Raises:
            TimeoutError: If the function takes too long
        """
        timeout = timeout or self.timeout
        
        # Set up signal handler
        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(timeout)
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            signal.alarm(0)  # Cancel alarm
            signal.signal(signal.SIGALRM, old_handler)  # Restore handler
    
    def _retry_request(self, func, *args, max_retries=3, timeout=None, **kwargs):
        """Execute a function with retry logic for rate limits and timeouts."""
        last_exception = None
        for attempt in range(max_retries):
            try:
                return self._with_timeout(func, *args, timeout=timeout, **kwargs)
            except TimeoutError:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise
            except (RedditAPIException, PrawcoreException) as e:
                last_exception = e
                if "ratelimit" in str(e).lower() or "429" in str(e):
                    retry_after = 60
                    if hasattr(e, "retry_after"):
                        retry_after = e.retry_after
                    if attempt < max_retries - 1:
                        time.sleep(retry_after)
                        continue
                raise
            except PRAWException:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise
        raise last_exception
    
    def search_subreddits(self, query: str, limit: int = 10, timeout: int = 15) -> list[str]:
        """Search for relevant subreddits by topic.
        
        Args:
            query: Search query
            limit: Maximum number of results
            timeout: Request timeout in seconds
        """
        subreddits = []
        try:
            results = self._retry_request(
                self.client.subreddits.search,
                query,
                limit=limit,
                timeout=timeout,
            )
            for subreddit in results:
                if hasattr(subreddit, 'display_name'):
                    subreddits.append(f"r/{subreddit.display_name}")
        except Exception as e:
            console = __import__('rich.console').console.Console()
            console.print(f"[yellow]Warning: Failed to search subreddits: {e}[/yellow]")
        return list(dict.fromkeys(subreddits))[:limit]
    
    def get_subreddit_posts(
        self,
        subreddit_name: str,
        limit: int = 50,
        time_filter: str = "month",
        timeout: int = 30,
    ) -> list[Submission]:
        """Get recent posts from a subreddit.
        
        Args:
            subreddit_name: Name of the subreddit
            limit: Maximum number of posts
            time_filter: Time range ("hour", "day", "week", "month", "year", "all")
            timeout: Request timeout in seconds
        """
        try:
            subreddit = self.client.subreddit(subreddit_name.lstrip("r/"))
            posts = self._retry_request(
                subreddit.top,
                time_filter=time_filter,
                limit=limit,
                timeout=timeout,
            )
            return list(posts)
        except Exception as e:
            console = __import__('rich.console').Console()
            console.print(f"[yellow]Warning: Failed to fetch posts from {subreddit_name}: {e}[/yellow]")
            return []
    
    def get_post_comments(
        self,
        post: Submission,
        limit: int = 50,
        timeout: int = 20,
        replace_more_limit: int = 5,
    ) -> list[Comment]:
        """Get top comments from a post.
        
        Args:
            post: PRAW Submission object
            limit: Maximum number of comments to return
            timeout: Request timeout in seconds
            replace_more_limit: Maximum number of MoreComment objects to replace
        """
        try:
            # Limit comment expansion to prevent hanging on deep threads
            post.comments.replace_more(limit=replace_more_limit, threshold=10)
            comments = list(post.comments)[:limit]
            return [c for c in comments if hasattr(c, 'body') and c.body != "[deleted]"]
        except Exception as e:
            console = __import__('rich.console').Console()
            console.print(f"[yellow]Warning: Failed to fetch comments: {e}[/yellow]")
            return []
    
    def get_subreddit_data(
        self,
        subreddit_name: str,
        post_limit: int = 50,
        comment_limit: int = 50,
        timeout: int = 30,
    ) -> dict:
        """Get posts and comments from a subreddit.
        
        Args:
            subreddit_name: Name of the subreddit
            post_limit: Maximum posts per subreddit
            comment_limit: Maximum comments per post
            timeout: Request timeout in seconds
        """
        posts = self.get_subreddit_posts(
            subreddit_name,
            limit=post_limit,
            timeout=timeout,
        )
        all_comments = []
        for post in posts[:5]:  # Only get comments from first 5 posts to save time
            comments = self.get_post_comments(
                post,
                limit=comment_limit,
                timeout=timeout,
            )
            all_comments.extend(comments)
        
        return {
            "subreddit": subreddit_name,
            "posts": posts,
            "comments": all_comments,
        }
