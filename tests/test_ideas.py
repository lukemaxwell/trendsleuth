"""Tests for the ideas module."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from trendsleuth.config import OpenAIConfig
from trendsleuth.ideas import (
    load_analysis_file,
    generate_ideas,
    format_ideas_as_markdown,
    AnalysisSignals,
    _parse_json_analysis,
    _parse_markdown_analysis,
    _extract_markdown_section,
    _extract_markdown_list,
)


class TestLoadAnalysisFile:
    """Tests for load_analysis_file."""
    
    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist."""
        with pytest.raises(ValueError, match="File not found"):
            load_analysis_file("/nonexistent/file.json")
    
    def test_load_json_file(self, tmp_path):
        """Test loading a JSON analysis file."""
        # Create test JSON file
        analysis_data = {
            "subreddit": "r/ai-agents",
            "analysis": {
                "summary": "Test summary",
                "topics": ["Topic 1", "Topic 2"],
                "pain_points": ["Pain 1", "Pain 2"],
                "questions": ["Question 1", "Question 2"],
            }
        }
        
        json_file = tmp_path / "analysis.json"
        json_file.write_text(json.dumps(analysis_data))
        
        signals = load_analysis_file(str(json_file))
        
        assert signals.niche == "ai agents"
        assert signals.summary == "Test summary"
        assert len(signals.topics) == 2
        assert len(signals.pain_points) == 2
        assert len(signals.questions) == 2
    
    def test_load_markdown_file(self, tmp_path):
        """Test loading a Markdown analysis file."""
        markdown_content = """# Trend Analysis: productivity tools

## Summary

This is a test summary.

## Trending Topics

1. Topic one
2. Topic two
3. Topic three

## Pain Points

1. Pain one
2. Pain two

## Questions & Curiosities

1. Question one
2. Question two
"""
        
        md_file = tmp_path / "analysis.md"
        md_file.write_text(markdown_content)
        
        signals = load_analysis_file(str(md_file))
        
        assert signals.niche == "productivity tools"
        assert "test summary" in signals.summary
        assert len(signals.topics) == 3
        assert len(signals.pain_points) == 2
        assert len(signals.questions) == 2


class TestParseJson:
    """Tests for JSON parsing."""
    
    def test_parse_valid_json(self):
        """Test parsing valid JSON."""
        json_str = json.dumps({
            "subreddit": "r/test-niche",
            "analysis": {
                "summary": "Test",
                "topics": ["T1", "T2"],
                "pain_points": ["P1"],
                "questions": ["Q1"],
            }
        })
        
        signals = _parse_json_analysis(json_str)
        assert signals.niche == "test niche"
        assert signals.summary == "Test"
    
    def test_parse_invalid_json(self):
        """Test parsing invalid JSON."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            _parse_json_analysis("not json")
    
    def test_parse_json_limits_lists(self):
        """Test that lists are limited to 10 items."""
        topics = [f"Topic {i}" for i in range(20)]
        json_str = json.dumps({
            "analysis": {
                "summary": "Test",
                "topics": topics,
                "pain_points": [],
                "questions": [],
            }
        })
        
        signals = _parse_json_analysis(json_str)
        assert len(signals.topics) == 10


class TestParseMarkdown:
    """Tests for Markdown parsing."""
    
    def test_parse_valid_markdown(self):
        """Test parsing valid Markdown."""
        markdown = """# Trend Analysis: AI Tools

## Summary

This is the summary text.

## Trending Topics

1. First topic
2. Second topic

## Pain Points

1. First pain
2. Second pain

## Questions & Curiosities

1. First question
"""
        
        signals = _parse_markdown_analysis(markdown)
        assert signals.niche == "AI Tools"
        assert "summary text" in signals.summary
        assert len(signals.topics) == 2
        assert signals.topics[0] == "First topic"
    
    def test_parse_markdown_missing_summary(self):
        """Test parsing Markdown without summary."""
        markdown = """# Trend Analysis: Test

## Topics

1. Topic one
"""
        
        with pytest.raises(ValueError, match="Could not extract summary"):
            _parse_markdown_analysis(markdown)
    
    def test_extract_markdown_section(self):
        """Test extracting a markdown section."""
        content = """## Section One

This is section one content.

## Section Two

This is section two.
"""
        
        result = _extract_markdown_section(content, "Section One")
        assert "section one content" in result
    
    def test_extract_markdown_list(self):
        """Test extracting a markdown list."""
        content = """## My List

1. First item
2. Second item
3. Third item

## Next Section
"""
        
        items = _extract_markdown_list(content, "My List")
        assert len(items) == 3
        assert items[0] == "First item"
        assert items[2] == "Third item"


class TestGenerateIdeas:
    """Tests for idea generation."""
    
    @pytest.fixture
    def config(self):
        """Create OpenAI config."""
        return OpenAIConfig(api_key="test_key")
    
    @pytest.fixture
    def signals(self):
        """Create test signals."""
        return AnalysisSignals(
            niche="productivity apps",
            summary="Users want better tools",
            topics=["Time tracking", "Focus tools"],
            pain_points=["Too expensive", "Too complex"],
            questions=["How to stay focused?"],
        )
    
    def test_generate_invalid_type(self, config, signals):
        """Test generating ideas with invalid type."""
        with pytest.raises(ValueError, match="Invalid idea type"):
            generate_ideas(config, signals, "invalid", 1)
    
    @patch('trendsleuth.ideas.ChatPromptTemplate')
    def test_generate_business_ideas(self, mock_template, config, signals):
        """Test generating business ideas."""
        # Mock the LLM response
        class MockBusinessIdea:
            name = "Test Business"
            description = "A test business"
            target_customer = "Developers"
            core_pain = "Time management"
            product_description = "An app"
            why_existing_fail = "Too complex"
            monetization = "Subscription"
            pricing = "$10/month"
            validation = "Beta program"
            
            def model_dump(self):
                return {
                    "name": self.name,
                    "description": self.description,
                    "target_customer": self.target_customer,
                    "core_pain": self.core_pain,
                    "product_description": self.product_description,
                    "why_existing_fail": self.why_existing_fail,
                    "monetization": self.monetization,
                    "pricing": self.pricing,
                    "validation": self.validation,
                }
        
        class MockResult:
            ideas = [MockBusinessIdea()]
        
        # Mock the chain
        mock_prompt_instance = MagicMock()
        mock_template.from_messages.return_value = mock_prompt_instance
        
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = MockResult()
        
        mock_intermediate = MagicMock()
        mock_intermediate.__or__.return_value = mock_chain
        mock_prompt_instance.__or__.return_value = mock_intermediate
        
        result = generate_ideas(config, signals, "business", 1)
        
        assert result["type"] == "business"
        assert len(result["ideas"]) == 1
        assert result["ideas"][0]["name"] == "Test Business"
    
    @patch('trendsleuth.ideas.ChatPromptTemplate')
    def test_generate_app_ideas(self, mock_template, config, signals):
        """Test generating app ideas."""
        # Mock the LLM response
        class MockAppIdea:
            name = "Test App"
            target_user = "Developers"
            problem = "Time tracking"
            features = ["Feature 1", "Feature 2"]
            unique_value = "Simple"
            mvp_scope = "Basic tracking"
            monetization = "Freemium"
            
            def model_dump(self):
                return {
                    "name": self.name,
                    "target_user": self.target_user,
                    "problem": self.problem,
                    "features": self.features,
                    "unique_value": self.unique_value,
                    "mvp_scope": self.mvp_scope,
                    "monetization": self.monetization,
                }
        
        class MockResult:
            ideas = [MockAppIdea()]
        
        # Mock the chain
        mock_prompt_instance = MagicMock()
        mock_template.from_messages.return_value = mock_prompt_instance
        
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = MockResult()
        
        mock_intermediate = MagicMock()
        mock_intermediate.__or__.return_value = mock_chain
        mock_prompt_instance.__or__.return_value = mock_intermediate
        
        result = generate_ideas(config, signals, "app", 1)
        
        assert result["type"] == "app"
        assert len(result["ideas"]) == 1
        assert result["ideas"][0]["name"] == "Test App"
    
    @patch('trendsleuth.ideas.ChatPromptTemplate')
    def test_generate_content_ideas(self, mock_template, config, signals):
        """Test generating content ideas."""
        # Mock the LLM response
        class MockContentIdea:
            title = "Test Content"
            format = "thread"
            target_audience = "Developers"
            angle = "Productivity hacks"
            engagement_reason = "Relatable"
            
            def model_dump(self):
                return {
                    "title": self.title,
                    "format": self.format,
                    "target_audience": self.target_audience,
                    "angle": self.angle,
                    "engagement_reason": self.engagement_reason,
                }
        
        class MockResult:
            ideas = [MockContentIdea()]
        
        # Mock the chain
        mock_prompt_instance = MagicMock()
        mock_template.from_messages.return_value = mock_prompt_instance
        
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = MockResult()
        
        mock_intermediate = MagicMock()
        mock_intermediate.__or__.return_value = mock_chain
        mock_prompt_instance.__or__.return_value = mock_intermediate
        
        result = generate_ideas(config, signals, "content", 1)
        
        assert result["type"] == "content"
        assert len(result["ideas"]) == 1
        assert result["ideas"][0]["title"] == "Test Content"


class TestFormatMarkdown:
    """Tests for markdown formatting."""
    
    def test_format_business_ideas(self):
        """Test formatting business ideas as markdown."""
        ideas_data = {
            "type": "business",
            "ideas": [{
                "name": "TaskMaster Pro",
                "description": "Smart task management",
                "target_customer": "Busy professionals",
                "core_pain": "Task overload",
                "product_description": "AI-powered task manager",
                "why_existing_fail": "Too complex",
                "monetization": "Subscription",
                "pricing": "$15/month",
                "validation": "Beta signup page",
            }]
        }
        
        output = format_ideas_as_markdown(ideas_data)
        
        assert "## Idea 1" in output
        assert "TaskMaster Pro" in output
        assert "Target Customer" in output
        assert "Busy professionals" in output
    
    def test_format_app_ideas(self):
        """Test formatting app ideas as markdown."""
        ideas_data = {
            "type": "app",
            "ideas": [{
                "name": "FocusFlow",
                "target_user": "Remote workers",
                "problem": "Distractions",
                "features": ["Pomodoro timer", "Block websites", "Analytics"],
                "unique_value": "Minimal interface",
                "mvp_scope": "Timer + blocking",
                "monetization": "One-time purchase",
            }]
        }
        
        output = format_ideas_as_markdown(ideas_data)
        
        assert "## Idea 1" in output
        assert "FocusFlow" in output
        assert "Pomodoro timer" in output
        assert "- Block websites" in output
    
    def test_format_content_ideas(self):
        """Test formatting content ideas as markdown."""
        ideas_data = {
            "type": "content",
            "ideas": [{
                "title": "Why productivity apps make you less productive",
                "format": "Twitter thread",
                "target_audience": "Tech workers",
                "angle": "Contrarian take on tools",
                "engagement_reason": "Challenges assumptions",
            }]
        }
        
        output = format_ideas_as_markdown(ideas_data)
        
        assert "## Idea 1" in output
        assert "productivity apps" in output
        assert "Twitter thread" in output
        assert "Contrarian take" in output
    
    def test_format_multiple_ideas(self):
        """Test formatting multiple ideas."""
        ideas_data = {
            "type": "content",
            "ideas": [
                {
                    "title": "Idea One",
                    "format": "post",
                    "target_audience": "Users",
                    "angle": "Angle 1",
                    "engagement_reason": "Reason 1",
                },
                {
                    "title": "Idea Two",
                    "format": "video",
                    "target_audience": "Viewers",
                    "angle": "Angle 2",
                    "engagement_reason": "Reason 2",
                }
            ]
        }
        
        output = format_ideas_as_markdown(ideas_data)
        
        assert "## Idea 1" in output
        assert "## Idea 2" in output
        assert "Idea One" in output
        assert "Idea Two" in output
