"""LLM-based trend analysis using OpenAI."""

from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser

from trendsleuth.config import OpenAIConfig


class TrendAnalysis(BaseModel):
    """Structured output for trend analysis."""
    
    topics: list[str] = Field(
        description="Top 10 trending topics in the subreddit"
    )
    pain_points: list[str] = Field(
        description="Top 7 pain points or challenges mentioned"
    )
    questions: list[str] = Field(
        description="Top 7 questions or curiosities expressed"
    )
    summary: str = Field(
        description="Brief summary of the overall trend sentiment"
    )
    sentiment: str = Field(
        description="Overall sentiment: positive, negative, or neutral"
    )


class Analyzer:
    """LLM-based trend analyzer."""
    
    def __init__(self, config: OpenAIConfig):
        """Initialize the analyzer with OpenAI configuration."""
        self.config = config
        self.model = ChatOpenAI(
            model=self.config.model,
            api_key=self.config.api_key,
            temperature=0.7,
        )
        self.parser = PydanticOutputParser(pydantic_object=TrendAnalysis)
    
    def analyze_subreddit_data(
        self,
        subreddit_name: str,
        posts: list,
        comments: list,
    ) -> Optional[TrendAnalysis]:
        """Analyze subreddit data and extract trends."""
        if not posts and not comments:
            return None
        
        # Prepare text content
        content_parts = [f"Subreddit: {subreddit_name}\n"]
        
        if posts:
            content_parts.append("\n=== Posts ===")
            for i, post in enumerate(posts[:15], 1):
                title = getattr(post, 'title', 'No title')
                self_text = getattr(post, 'selftext', '')
                content_parts.append(f"\nPost {i}: {title}")
                if self_text:
                    content_parts.append(f"  Body: {self_text[:500]}")
        
        if comments:
            content_parts.append("\n=== Comments ===")
            for i, comment in enumerate(comments[:100], 1):
                body = getattr(comment, 'body', '')
                if body and body != "[deleted]":
                    content_parts.append(f"\nComment {i}: {body[:300]}")
        
        full_content = "\n".join(content_parts)
        
        # Create prompt
        prompt_template = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are a trend analysis expert for content creators.
Your task is to analyze Reddit discussions and extract actionable insights.

Format your response as JSON with these fields:
- topics: Top 10 trending topics
- pain_points: Top 7 pain points or challenges
- questions: Top 7 questions or curiosities
- summary: Brief overall sentiment summary
- sentiment: Overall sentiment (positive, negative, or neutral)

Be concise and focused on what content creators should know."""
            ),
            (
                "human",
                "Analyze this Reddit data:\n{content}\n\n{format_instructions}"
            ),
        ])
        
        try:
            chain = prompt_template | self.model | self.parser
            result = chain.invoke({
                "content": full_content[:15000],
                "format_instructions": self.parser.get_format_instructions(),
            })
            return result
        except Exception:
            return None
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate API cost based on token usage."""
        # gpt-4o-mini pricing (as of 2024)
        input_price_per_1k = 0.00015
        output_price_per_1k = 0.0006
        
        cost = (prompt_tokens * input_price_per_1k / 1000 + 
                completion_tokens * output_price_per_1k / 1000)
        return cost
