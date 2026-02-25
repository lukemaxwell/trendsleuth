"""Configuration and environment settings for TrendSleuth."""

import os

from pydantic import BaseModel, Field


class RedditConfig(BaseModel):
    """Configuration for Reddit API access."""

    client_id: str = Field(
        default_factory=lambda: os.environ.get("REDDIT_CLIENT_ID", "")
    )
    client_secret: str = Field(
        default_factory=lambda: os.environ.get("REDDIT_CLIENT_SECRET", "")
    )
    user_agent: str = Field(
        default_factory=lambda: os.environ.get("REDDIT_USER_AGENT", "TrendSleuth/0.1.0")
    )


class OpenAIConfig(BaseModel):
    """Configuration for OpenAI API access."""

    api_key: str = Field(default_factory=lambda: os.environ.get("OPENAI_API_KEY", ""))
    model: str = "gpt-4o-mini"


class BraveConfig(BaseModel):
    """Configuration for Brave Search API access."""

    api_key: str = Field(default_factory=lambda: os.environ.get("BRAVE_API_KEY", ""))
    rate_limit_rps: float = 1.0


class AppConfig(BaseModel):
    """Main application configuration."""

    verbose: bool = False
    limit: int = 50
    output_format: str = "markdown"

    # Rate limiting
    max_retries: int = 3
    retry_delay: float = 1.0

    # Timeouts
    request_timeout: int = 30
    search_timeout: int = 15
    comment_timeout: int = 20


def get_config() -> tuple[RedditConfig, OpenAIConfig, AppConfig, BraveConfig]:
    """Get all configuration objects."""
    reddit_config = RedditConfig()
    openai_config = OpenAIConfig()
    app_config = AppConfig()
    brave_config = BraveConfig()
    return reddit_config, openai_config, app_config, brave_config


def validate_env_vars() -> list[str]:
    """Check for required environment variables."""
    missing = []
    if not os.environ.get("REDDIT_CLIENT_ID"):
        missing.append("REDDIT_CLIENT_ID")
    if not os.environ.get("REDDIT_CLIENT_SECRET"):
        missing.append("REDDIT_CLIENT_SECRET")
    if not os.environ.get("OPENAI_API_KEY"):
        missing.append("OPENAI_API_KEY")
    return missing


def validate_brave_env() -> bool:
    """Check if Brave API key is configured.

    Returns:
        True if BRAVE_API_KEY is set
    """
    return bool(os.environ.get("BRAVE_API_KEY"))
