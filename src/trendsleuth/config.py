"""Configuration and environment settings for TrendSleuth."""

import os
from typing import Optional

from pydantic import BaseModel, Field


class RedditConfig(BaseModel):
    """Configuration for Reddit API access."""

    client_id: str = Field(default_factory=lambda: os.environ.get("REDDIT_CLIENT_ID", ""))
    client_secret: str = Field(default_factory=lambda: os.environ.get("REDDIT_CLIENT_SECRET", ""))
    user_agent: str = Field(default_factory=lambda: os.environ.get("REDDIT_USER_AGENT", "TrendSleuth/0.1.0"))


class OpenAIConfig(BaseModel):
    """Configuration for OpenAI API access."""

    api_key: str = Field(default_factory=lambda: os.environ.get("OPENAI_API_KEY", ""))
    model: str = "gpt-4o-mini"


class AppConfig(BaseModel):
    """Main application configuration."""

    verbose: bool = False
    limit: int = 50
    output_format: str = "markdown"
    
    # Rate limiting
    max_retries: int = 3
    retry_delay: float = 1.0


def get_config() -> tuple[RedditConfig, OpenAIConfig, AppConfig]:
    """Get all configuration objects."""
    reddit_config = RedditConfig()
    openai_config = OpenAIConfig()
    app_config = AppConfig()
    return reddit_config, openai_config, app_config


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
