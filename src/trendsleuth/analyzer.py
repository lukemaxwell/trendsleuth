"""LLM-based trend analysis using OpenAI."""

import logging
from typing import Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, SecretStr
from langchain_core.output_parsers import PydanticOutputParser

from trendsleuth.config import OpenAIConfig

logger = logging.getLogger(__name__)


class Evidence(BaseModel):
    """Evidence item with source attribution."""

    source: str = Field(description="Source type: 'reddit' or 'web'")
    quote: str = Field(description="Verbatim quote from the source")
    url: str = Field(description="URL to the source")
    date: Optional[str] = Field(
        default=None, description="Date in ISO format YYYY-MM-DD"
    )


class TrendAnalysis(BaseModel):
    """Structured output for trend analysis."""

    topics: list[str] = Field(description="Top 10 trending topics in the subreddit")
    pain_points: list[str] = Field(
        description="Top 7 pain points or challenges mentioned"
    )
    questions: list[str] = Field(description="Top 7 questions or curiosities expressed")
    summary: str = Field(description="Brief summary of the overall trend sentiment")
    sentiment: str = Field(
        description="Overall sentiment: positive, negative, or neutral"
    )
    evidence: Optional[list[Evidence]] = Field(
        default=None, description="Evidence items with verbatim quotes, URLs, and dates"
    )


class NicheList(BaseModel):
    """Structured output for niche generation."""

    niches: list[str] = Field(description="List of specific niche ideas")


class Analyzer:
    """LLM-based trend analyzer."""

    def __init__(self, config: OpenAIConfig):
        """Initialize the analyzer with OpenAI configuration."""
        self.config = config
        self.model = ChatOpenAI(
            model=self.config.model,
            api_key=SecretStr(self.config.api_key),  # type: ignore[arg-type]
            temperature=0.7,
        )
        self.parser = PydanticOutputParser(pydantic_object=TrendAnalysis)

    def analyze_subreddit_data(
        self,
        subreddit_name: str,
        posts: list,
        comments: list,
        include_evidence: bool = False,
    ) -> Optional[TrendAnalysis]:
        """Analyze subreddit data and extract trends.

        Args:
            subreddit_name: Name of the subreddit
            posts: List of Reddit posts
            comments: List of Reddit comments
            include_evidence: If True, include evidence with quotes and URLs

        Returns:
            TrendAnalysis object or None if analysis fails
        """
        if not posts and not comments:
            return None

        # Prepare text content with metadata for evidence
        content_parts = [f"Subreddit: {subreddit_name}\n"]

        if posts:
            content_parts.append("\n=== Posts ===")
            for i, post in enumerate(posts[:15], 1):
                title = getattr(post, "title", "No title")
                self_text = getattr(post, "selftext", "")
                url = (
                    f"https://reddit.com{getattr(post, 'permalink', '')}"
                    if hasattr(post, "permalink")
                    else ""
                )
                created_utc = getattr(post, "created_utc", None)
                date_str = (
                    datetime.fromtimestamp(created_utc).strftime("%Y-%m-%d")
                    if created_utc
                    else "unknown"
                )

                content_parts.append(
                    f"\nPost {i} [URL: {url}] [Date: {date_str}]: {title}"
                )
                if self_text:
                    content_parts.append(f"  Body: {self_text[:500]}")

        if comments:
            content_parts.append("\n=== Comments ===")
            for i, comment in enumerate(comments[:100], 1):
                body = getattr(comment, "body", "")
                if body and body != "[deleted]":
                    url = (
                        f"https://reddit.com{getattr(comment, 'permalink', '')}"
                        if hasattr(comment, "permalink")
                        else ""
                    )
                    created_utc = getattr(comment, "created_utc", None)
                    date_str = (
                        datetime.fromtimestamp(created_utc).strftime("%Y-%m-%d")
                        if created_utc
                        else "unknown"
                    )

                    content_parts.append(
                        f"\nComment {i} [URL: {url}] [Date: {date_str}]: {body[:300]}"
                    )

        full_content = "\n".join(content_parts)

        # Create prompt with optional evidence instructions
        evidence_instructions = ""
        if include_evidence:
            evidence_instructions = """
IMPORTANT: Include an 'evidence' array with 5-10 supporting quotes:
- Use VERBATIM quotes from the content (do not paraphrase or modify)
- Include the exact URL provided in square brackets
- Include the date in YYYY-MM-DD format if provided, otherwise set to null
- Source should be "reddit" for all items
- Choose quotes that best support the topics, pain points, and questions identified
"""

        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a trend analysis expert for content creators.
Your task is to analyze Reddit discussions and extract actionable insights.

Format your response as JSON with these fields:
- topics: Top 10 trending topics
- pain_points: Top 7 pain points or challenges
- questions: Top 7 questions or curiosities
- summary: Brief overall sentiment summary
- sentiment: Overall sentiment (positive, negative, or neutral)"""
                    + evidence_instructions
                    + """

Be concise and focused on what content creators should know.""",
                ),
                (
                    "human",
                    "Analyze this Reddit data:\n{content}\n\n{format_instructions}",
                ),
            ]
        )

        try:
            chain = prompt_template | self.model | self.parser
            result = chain.invoke(
                {
                    "content": full_content[:15000],
                    "format_instructions": self.parser.get_format_instructions(),
                }
            )
            return result
        except Exception:
            return None

    def generate_niches(
        self,
        theme: str,
        count: int = 15,
    ) -> Optional[list[str]]:
        """Generate niche ideas for a given theme.

        Args:
            theme: Topic or domain to generate niches within
            count: Number of niches to generate

        Returns:
            List of niche ideas or None if generation fails
        """
        niche_parser = PydanticOutputParser(pydantic_object=NicheList)

        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a niche ideation expert for content creators and entrepreneurs.

Generate specific, concrete niche ideas within the given theme.

RULES:
- Each niche should be 3-5 words
- Be specific and concrete, not broad
- Describe a user context, task, problem, or constraint
- Avoid generic categories like "travel apps" or "fitness tools"
- Avoid industry buzzwords: platform, ecosystem, industry, AI platform, SaaS solution
- Focus on specific use cases, workflows, constraints, or user situations

GOOD examples:
- solo travel itinerary planning
- group trip coordination tools
- budget travel optimization apps
- last-minute activity discovery
- remote team async collaboration
- freelance invoice tracking systems

BAD examples:
- travel platform (too broad)
- fitness ecosystem (buzzword)
- AI productivity tools (generic)
- SaaS solutions (industry jargon)""",
                ),
                (
                    "human",
                    "Generate {count} specific niche ideas for the theme: {theme}\n\n{format_instructions}",
                ),
            ]
        )

        try:
            chain = prompt_template | self.model | niche_parser
            result = chain.invoke(
                {
                    "theme": theme,
                    "count": count,
                    "format_instructions": niche_parser.get_format_instructions(),
                }
            )
            return result.niches[:count]  # Ensure we return exactly count items
        except Exception as e:
            logger.error(f"Failed to generate niches: {e}")
            return None

    def extract_quotes_from_text(
        self,
        text: str,
        niche: str,
        url: str,
        max_quotes: int = 2,
    ) -> list[Evidence]:
        """Extract pain-related quotes from web page text.

        Args:
            text: Page text content
            niche: The niche being analyzed
            url: Source URL
            max_quotes: Maximum quotes to extract

        Returns:
            List of Evidence items
        """

        class QuoteList(BaseModel):
            """Structured output for quote extraction."""

            quotes: list[dict] = Field(
                description="List of extracted quotes with optional dates"
            )

        quote_parser = PydanticOutputParser(pydantic_object=QuoteList)

        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert at extracting pain points and complaints from text.

Extract 0-{max_quotes} verbatim quotes that express:
- Problems or frustrations with {niche}
- Complaints or negative experiences
- Challenges or difficulties
- Unmet needs or wishes

CRITICAL RULES:
- Use EXACT quotes from the text (do not paraphrase)
- Each quote should be 1-3 sentences
- Only extract quotes clearly related to {niche}
- If the page has a published/posted date, include it in ISO format (YYYY-MM-DD)
- If no clear date, set date to null
- DO NOT invent or guess dates

Return JSON array of objects:
{{"quote": "exact text", "date": "YYYY-MM-DD or null"}}""",
                ),
                (
                    "human",
                    "Extract pain quotes from this text:\n\n{text}\n\n{format_instructions}",
                ),
            ]
        )

        try:
            # Truncate text to avoid token limits
            truncated_text = text[:5000]

            chain = prompt_template | self.model | quote_parser
            result = chain.invoke(
                {
                    "text": truncated_text,
                    "niche": niche,
                    "max_quotes": max_quotes,
                    "format_instructions": quote_parser.get_format_instructions(),
                }
            )

            # Convert to Evidence objects
            evidence_items = []
            for item in result.quotes[:max_quotes]:
                evidence_items.append(
                    Evidence(
                        source="web",
                        quote=item.get("quote", ""),
                        url=url,
                        date=item.get("date"),
                    )
                )

            return evidence_items

        except Exception as e:
            logger.debug(f"Failed to extract quotes from {url}: {e}")
            return []

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate API cost based on token usage."""
        # gpt-4o-mini pricing (as of 2024)
        input_price_per_1k = 0.00015
        output_price_per_1k = 0.0006

        cost = (
            prompt_tokens * input_price_per_1k / 1000
            + completion_tokens * output_price_per_1k / 1000
        )
        return cost
