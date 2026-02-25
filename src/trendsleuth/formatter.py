"""Output formatting for trend analysis results."""

import json
from typing import Optional

from trendsleuth.analyzer import TrendAnalysis


def format_markdown(
    subreddit: str,
    analysis: TrendAnalysis,
    token_usage: Optional[dict] = None,
    cost: Optional[float] = None,
) -> str:
    """Format analysis results as markdown."""
    lines = [
        f"# Trend Analysis: {subreddit}\n",
        f"**Generated at:** {get_timestamp()}\n",
    ]
    
    # Summary
    lines.extend([
        "## Summary\n",
        analysis.summary,
        "\n",
    ])
    
    # Topics
    lines.extend([
        "## Trending Topics\n",
    ])
    for i, topic in enumerate(analysis.topics, 1):
        lines.append(f"{i}. {topic}")
    lines.append("")
    
    # Pain Points
    lines.extend([
        "## Pain Points\n",
    ])
    for i, pain_point in enumerate(analysis.pain_points, 1):
        lines.append(f"{i}. {pain_point}")
    lines.append("")
    
    # Questions
    lines.extend([
        "## Questions & Curiosities\n",
    ])
    for i, question in enumerate(analysis.questions, 1):
        lines.append(f"{i}. {question}")
    lines.append("")
    
    # Evidence section if present
    if analysis.evidence:
        lines.extend([
            "## Evidence (Recent)\n",
        ])
        for evidence_item in analysis.evidence:
            date_str = evidence_item.date if evidence_item.date else "unknown"
            source_label = "WEB" if evidence_item.source == "web" else "REDDIT"
            lines.append(f"- [{date_str}] [{source_label}] \"{evidence_item.quote}\" — {evidence_item.url}")
        lines.append("")
    
    # Metadata
    if token_usage or cost is not None:
        lines.extend([
            "## Metrics\n",
        ])
        if token_usage:
            total_tokens = token_usage.get("input_tokens", 0) + token_usage.get("output_tokens", 0)
            lines.append(f"- **Total tokens used:** {total_tokens:,}")
        if cost is not None:
            lines.append(f"- **Estimated cost:** ${cost:.4f}")
        lines.append("")
    
    return "\n".join(lines)


def format_json(
    subreddit: str,
    analysis: TrendAnalysis,
    token_usage: Optional[dict] = None,
    cost: Optional[float] = None,
) -> str:
    """Format analysis results as JSON."""
    result = {
        "subreddit": subreddit,
        "timestamp": get_timestamp(),
        "analysis": {
            "topics": analysis.topics,
            "pain_points": analysis.pain_points,
            "questions": analysis.questions,
            "summary": analysis.summary,
            "sentiment": analysis.sentiment,
        },
    }
    
    # Add evidence if present
    if analysis.evidence:
        result["analysis"]["evidence"] = [
            {
                "source": evidence_item.source,
                "quote": evidence_item.quote,
                "url": evidence_item.url,
                "date": evidence_item.date,
            }
            for evidence_item in analysis.evidence
        ]
    
    if token_usage:
        result["token_usage"] = token_usage
    
    if cost is not None:
        result["estimated_cost"] = cost
    
    return json.dumps(result, indent=2)


def get_timestamp() -> str:
    """Get current timestamp string."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
