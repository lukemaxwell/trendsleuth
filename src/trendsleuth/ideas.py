"""Idea generation from TrendSleuth analysis."""

import json
import logging
import re
from pathlib import Path
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser

from trendsleuth.config import OpenAIConfig

logger = logging.getLogger(__name__)


class BusinessIdea(BaseModel):
    """Structured business idea."""

    name: str = Field(description="Business name")
    description: str = Field(description="One-line description")
    target_customer: str = Field(description="Target customer segment")
    core_pain: str = Field(description="Core pain being solved")
    product_description: str = Field(description="Product/service description")
    why_existing_fail: str = Field(description="Why existing solutions fail")
    monetization: str = Field(description="Monetization model")
    pricing: str = Field(description="Pricing approach")
    validation: str = Field(description="Early validation strategy")


class AppIdea(BaseModel):
    """Structured app/product idea."""

    name: str = Field(description="App name")
    target_user: str = Field(description="Target user")
    problem: str = Field(description="Problem solved")
    features: list[str] = Field(description="Core features (3-5 items)")
    unique_value: str = Field(description="Unique value proposition")
    mvp_scope: str = Field(description="MVP scope - what to build first")
    monetization: str = Field(description="Monetization approach")


class ContentIdea(BaseModel):
    """Structured content idea."""

    title: str = Field(description="Title or hook")
    format: str = Field(description="Format (thread, post, video, etc.)")
    target_audience: str = Field(description="Target audience")
    angle: str = Field(description="Core angle or thesis")
    engagement_reason: str = Field(description="Why it will be engaging/viral")


class BusinessIdeasList(BaseModel):
    """List of business ideas."""

    ideas: list[BusinessIdea] = Field(description="List of business ideas")


class AppIdeasList(BaseModel):
    """List of app ideas."""

    ideas: list[AppIdea] = Field(description="List of app ideas")


class ContentIdeasList(BaseModel):
    """List of content ideas."""

    ideas: list[ContentIdea] = Field(description="List of content ideas")


class AnalysisSignals(BaseModel):
    """Extracted signals from analysis."""

    niche: Optional[str] = None
    summary: str
    topics: list[str]
    pain_points: list[str]
    questions: list[str]


def load_analysis_file(filepath: str) -> AnalysisSignals:
    """Load and parse TrendSleuth analysis file.

    Args:
        filepath: Path to analysis file (JSON or Markdown)

    Returns:
        Extracted analysis signals

    Raises:
        ValueError: If file cannot be parsed
    """
    path = Path(filepath)

    if not path.exists():
        raise ValueError(f"File not found: {filepath}")

    content = path.read_text()

    # Detect format
    if filepath.endswith(".json"):
        return _parse_json_analysis(content)
    else:
        return _parse_markdown_analysis(content)


def _parse_json_analysis(content: str) -> AnalysisSignals:
    """Parse JSON analysis file."""
    try:
        data = json.loads(content)
        analysis = data.get("analysis", {})

        # Extract niche from subreddit name if available
        niche = None
        subreddit = data.get("subreddit", "")
        if subreddit:
            # Remove r/ prefix and clean up
            niche = subreddit.replace("r/", "").replace("-", " ")

        return AnalysisSignals(
            niche=niche,
            summary=analysis.get("summary", ""),
            topics=analysis.get("topics", [])[:10],
            pain_points=analysis.get("pain_points", [])[:10],
            questions=analysis.get("questions", [])[:10],
        )
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Invalid JSON analysis file: {e}")


def _parse_markdown_analysis(content: str) -> AnalysisSignals:
    """Parse Markdown analysis file."""
    # Extract niche from title
    niche = None
    title_match = re.search(r"# Trend Analysis: (.+)", content)
    if title_match:
        niche = title_match.group(1).strip()

    # Extract summary
    summary = _extract_markdown_section(content, "Summary")

    # Extract lists
    topics = _extract_markdown_list(content, "Trending Topics")
    pain_points = _extract_markdown_list(content, "Pain Points")
    # Try both "Questions & Curiosities" and "Questions"
    questions = _extract_markdown_list(content, "Questions & Curiosities")
    if not questions:
        questions = _extract_markdown_list(content, "Questions")

    if not summary:
        raise ValueError("Could not extract summary from markdown file")

    return AnalysisSignals(
        niche=niche,
        summary=summary,
        topics=topics[:10],
        pain_points=pain_points[:10],
        questions=questions[:10],
    )


def _extract_markdown_section(content: str, heading: str) -> str:
    """Extract text from a markdown section."""
    # Match section heading and get content until next heading
    # Allow for optional whitespace/empty lines after the heading
    pattern = rf"## {heading}\s*\n+(.+?)(?=\n## |\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def _extract_markdown_list(content: str, heading: str) -> list[str]:
    """Extract list items from a markdown section."""
    # Match section heading and get content until next heading or end
    # Allow for optional whitespace/empty lines after the heading
    pattern = rf"## {heading}\s*\n+(.+?)(?=\n## |\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        section_content = match.group(1).strip()
        # Extract numbered list items
        items = re.findall(r"^\d+\.\s*(.+)$", section_content, re.MULTILINE)
        return [item.strip() for item in items]
    return []


def generate_ideas(
    config: OpenAIConfig,
    signals: AnalysisSignals,
    idea_type: str,
    count: int = 1,
) -> dict:
    """Generate ideas from analysis signals.

    Args:
        config: OpenAI configuration
        signals: Analysis signals
        idea_type: Type of ideas ('business', 'app', or 'content')
        count: Number of ideas to generate

    Returns:
        Dictionary with type and ideas list

    Raises:
        ValueError: If idea_type is invalid
    """
    if idea_type not in ("business", "app", "content"):
        raise ValueError(f"Invalid idea type: {idea_type}")

    # Build context string
    context_parts = []
    if signals.niche:
        context_parts.append(f"Niche: {signals.niche}")
    context_parts.append(f"Summary: {signals.summary}")

    if signals.pain_points:
        context_parts.append("\nTop Pain Points:")
        for i, pain in enumerate(signals.pain_points[:10], 1):
            context_parts.append(f"{i}. {pain}")

    if signals.topics:
        context_parts.append("\nTop Topics:")
        for i, topic in enumerate(signals.topics[:10], 1):
            context_parts.append(f"{i}. {topic}")

    if signals.questions:
        context_parts.append("\nTop Questions:")
        for i, question in enumerate(signals.questions[:10], 1):
            context_parts.append(f"{i}. {question}")

    context = "\n".join(context_parts)

    # Generate based on type
    if idea_type == "business":
        return _generate_business_ideas(config, context, count)
    elif idea_type == "app":
        return _generate_app_ideas(config, context, count)
    else:  # content
        return _generate_content_ideas(config, context, count)


def _generate_business_ideas(
    config: OpenAIConfig,
    context: str,
    count: int,
) -> dict:
    """Generate business ideas."""
    model = ChatOpenAI(
        model=config.model,
        api_key=config.api_key,
        temperature=0.8,
    )

    parser = PydanticOutputParser(pydantic_object=BusinessIdeasList)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a business ideation expert.

Generate {count} structured business ideas based on the analysis provided.

REQUIREMENTS:
- Be specific and concrete, not generic
- Address real pain points from the analysis
- Focus on realistic, actionable businesses
- Avoid buzzwords and vague descriptions
- Each idea should be unique and differentiated

Each idea must include:
- Name (2-4 words, memorable)
- One-line description (clear value prop)
- Target customer (specific segment)
- Core pain being solved (from analysis)
- Product description (what you're building)
- Why existing solutions fail (specific gaps)
- Monetization model (clear revenue approach)
- Pricing approach (concrete pricing strategy)
- Early validation strategy (how to test demand)

Output structured JSON.""",
            ),
            ("human", "Analysis:\n{context}\n\n{format_instructions}"),
        ]
    )

    try:
        chain = prompt | model | parser
        result = chain.invoke(
            {
                "context": context,
                "count": count,
                "format_instructions": parser.get_format_instructions(),
            }
        )

        return {
            "type": "business",
            "ideas": [idea.model_dump() for idea in result.ideas[:count]],
        }
    except Exception as e:
        logger.error(f"Failed to generate business ideas: {e}")
        raise


def _generate_app_ideas(
    config: OpenAIConfig,
    context: str,
    count: int,
) -> dict:
    """Generate app/product ideas."""
    model = ChatOpenAI(
        model=config.model,
        api_key=config.api_key,
        temperature=0.8,
    )

    parser = PydanticOutputParser(pydantic_object=AppIdeasList)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a product ideation expert.

Generate {count} structured app/product ideas based on the analysis provided.

REQUIREMENTS:
- Focus on realistic MVPs, not full platforms
- Address real pain points from the analysis
- Be specific about features and scope
- Avoid generic "AI platform" or "ecosystem" ideas
- Each idea should be unique

Each idea must include:
- App name (2-3 words, memorable)
- Target user (specific user persona)
- Problem solved (clear problem statement)
- Core features (3-5 bullet points, specific)
- Unique value (what makes this different)
- MVP scope (what to build first, be realistic)
- Monetization approach (clear revenue model)

Output structured JSON.""",
            ),
            ("human", "Analysis:\n{context}\n\n{format_instructions}"),
        ]
    )

    try:
        chain = prompt | model | parser
        result = chain.invoke(
            {
                "context": context,
                "count": count,
                "format_instructions": parser.get_format_instructions(),
            }
        )

        return {
            "type": "app",
            "ideas": [idea.model_dump() for idea in result.ideas[:count]],
        }
    except Exception as e:
        logger.error(f"Failed to generate app ideas: {e}")
        raise


def _generate_content_ideas(
    config: OpenAIConfig,
    context: str,
    count: int,
) -> dict:
    """Generate content ideas."""
    model = ChatOpenAI(
        model=config.model,
        api_key=config.api_key,
        temperature=0.9,
    )

    parser = PydanticOutputParser(pydantic_object=ContentIdeasList)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a content strategy expert.

Generate {count} high-engagement content ideas based on the analysis provided.

REQUIREMENTS:
- Be specific and opinionated
- Address real questions or pain points from the analysis
- Focus on insight-driven or contrarian angles
- Avoid generic topics
- Each idea should be unique and engaging

Each idea must include:
- Title/hook (compelling, specific)
- Format (thread, post, video, article, etc.)
- Target audience (who this is for)
- Core angle/thesis (the key insight or argument)
- Why engaging (what makes this viral/shareable)

Content should be educational, entertaining, or thought-provoking.
Avoid listicles and generic how-to content.

Output structured JSON.""",
            ),
            ("human", "Analysis:\n{context}\n\n{format_instructions}"),
        ]
    )

    try:
        chain = prompt | model | parser
        result = chain.invoke(
            {
                "context": context,
                "count": count,
                "format_instructions": parser.get_format_instructions(),
            }
        )

        return {
            "type": "content",
            "ideas": [idea.model_dump() for idea in result.ideas[:count]],
        }
    except Exception as e:
        logger.error(f"Failed to generate content ideas: {e}")
        raise


def format_ideas_as_markdown(ideas_data: dict) -> str:
    """Format ideas as markdown.

    Args:
        ideas_data: Dictionary with type and ideas list

    Returns:
        Markdown formatted string
    """
    idea_type = ideas_data["type"]
    ideas = ideas_data["ideas"]

    lines = []

    for i, idea in enumerate(ideas, 1):
        lines.append(f"## Idea {i}")
        lines.append("")

        if idea_type == "business":
            lines.append(f"**{idea['name']}**")
            lines.append("")
            lines.append(f"_{idea['description']}_")
            lines.append("")
            lines.append(f"**Target Customer:** {idea['target_customer']}")
            lines.append("")
            lines.append(f"**Core Pain:** {idea['core_pain']}")
            lines.append("")
            lines.append(f"**Product:** {idea['product_description']}")
            lines.append("")
            lines.append(
                f"**Why Existing Solutions Fail:** {idea['why_existing_fail']}"
            )
            lines.append("")
            lines.append(f"**Monetization:** {idea['monetization']}")
            lines.append("")
            lines.append(f"**Pricing:** {idea['pricing']}")
            lines.append("")
            lines.append(f"**Validation Strategy:** {idea['validation']}")
            lines.append("")

        elif idea_type == "app":
            lines.append(f"**{idea['name']}**")
            lines.append("")
            lines.append(f"**Target User:** {idea['target_user']}")
            lines.append("")
            lines.append(f"**Problem:** {idea['problem']}")
            lines.append("")
            lines.append("**Core Features:**")
            for feature in idea["features"]:
                lines.append(f"- {feature}")
            lines.append("")
            lines.append(f"**Unique Value:** {idea['unique_value']}")
            lines.append("")
            lines.append(f"**MVP Scope:** {idea['mvp_scope']}")
            lines.append("")
            lines.append(f"**Monetization:** {idea['monetization']}")
            lines.append("")

        else:  # content
            lines.append(f"**{idea['title']}**")
            lines.append("")
            lines.append(f"**Format:** {idea['format']}")
            lines.append("")
            lines.append(f"**Target Audience:** {idea['target_audience']}")
            lines.append("")
            lines.append(f"**Angle:** {idea['angle']}")
            lines.append("")
            lines.append(f"**Why It Works:** {idea['engagement_reason']}")
            lines.append("")

    return "\n".join(lines)
