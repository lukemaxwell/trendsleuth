"""Reddit API client using PRAW for synchronous operations."""

import time
from typing import Optional

import praw
from praw.models import Submission, Comment
from praw.exceptions import RedditAPIException, PRAWException
from prawcore.exceptions import PrawcoreException

from trendsleuth.config import RedditConfig


class RedditClient:
    """Client for interacting with Reddit API."""
    
    def __init__(self, config: RedditConfig):
        """Initialize the Reddit client."""
        self.config = config
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
    
    def _retry_request(self, func, *args, max_retries=3, **kwargs):
        """Execute a function with retry logic for rate limits."""
        last_exception = None
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
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
    
    def search_subreddits(self, query: str, limit: int = 10) -> list[str]:
        """Search for relevant subreddits by topic."""
        subreddits = []
        try:
            results = self.client.subreddits.search(query, limit=limit)
            for subreddit in results:
                if hasattr(subreddit, 'display_name'):
                    subreddits.append(f"r/{subreddit.display_name}")
        except Exception as e:
            pass
        return list(dict.fromkeys(subreddits))[:limit]
    
    def get_subreddit_posts(
        self,
        subreddit_name: str,
        limit: int = 50,
        time_filter: str = "month",
    ) -> list[Submission]:
        """Get recent posts from a subreddit."""
        try:
            subreddit = self.client.subreddit(subreddit_name.lstrip("r/"))
            posts = self._retry_request(
                subreddit.top,
                time_filter=time_filter,
                limit=limit,
            )
            return list(posts)
        except Exception:
            return []
    
    def get_post_comments(self, post: Submission, limit: int = 50) -> list[Comment]:
        """Get top comments from a post."""
        try:
            post.comments.replace_more(limit=0)
            comments = list(post.comments)[:limit]
            return [c for c in comments if hasattr(c, 'body') and c.body != "[deleted]"]
        except Exception:
            return []
    
    def get_subreddit_data(
        self,
        subreddit_name: str,
        post_limit: int = 50,
        comment_limit: int = 50,
    ) -> dict:
        """Get posts and comments from a subreddit."""
        posts = self.get_subreddit_posts(subreddit_name, limit=post_limit)
        all_comments = []
        for post in posts:
            comments = self.get_post_comments(post, limit=comment_limit)
            all_comments.extend(comments)
        
        return {
            "subreddit": subreddit_name,
            "posts": posts,
            "comments": all_comments,
        }
