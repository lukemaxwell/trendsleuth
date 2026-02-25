from unittest.mock import Mock

import pytest
from rich.progress import Progress

from trendsleuth.reddit import RedditClient


@pytest.fixture
def mock_reddit_client():
    """Create a mock Reddit client."""
    return Mock(autospec=RedditClient)


@pytest.fixture
def mock_progress():
    """Create a mock progress instance."""
    return Mock(autospec=Progress)
