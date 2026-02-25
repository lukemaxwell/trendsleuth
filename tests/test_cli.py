"""Tests for the CLI module."""

import json
import pytest
from unittest.mock import Mock, patch
from typer.testing import CliRunner

from trendsleuth.cli import (
    app,
    validate_configuration,
    discover_subreddits,
    fetch_subreddit_data,
    analyze_content,
    format_output,
    write_output,
    print_summary,
    run_analysis_pipeline,
    AnalysisContext,
    CLIError,
)
from trendsleuth.config import RedditConfig, OpenAIConfig
from trendsleuth.analyzer import TrendAnalysis


runner = CliRunner()


class TestValidateConfiguration:
    """Tests for validate_configuration function."""

    @patch("trendsleuth.cli.validate_env_vars")
    def test_valid_configuration(self, mock_validate):
        """Test with valid configuration (no missing vars)."""
        mock_validate.return_value = []

        result = validate_configuration()

        assert result is True
        mock_validate.assert_called_once()

    @patch("trendsleuth.cli.validate_env_vars")
    @patch("trendsleuth.cli.console")
    def test_invalid_configuration(self, mock_console, mock_validate):
        """Test with invalid configuration (missing vars)."""
        mock_validate.return_value = ["OPENAI_API_KEY", "REDDIT_CLIENT_ID"]

        result = validate_configuration()

        assert result is False
        mock_validate.assert_called_once()
        mock_console.print.assert_called_once()


class TestDiscoverSubreddits:
    """Tests for discover_subreddits function."""

    @pytest.fixture
    def mock_reddit_client(self):
        """Create a mock Reddit client."""
        return Mock()

    def test_with_explicit_subreddits(self, mock_reddit_client):
        """Test when subreddits are explicitly provided."""
        result = discover_subreddits(
            mock_reddit_client,
            niche="AI",
            subreddits="r/ai,r/machinelearning,r/artificial",
        )

        assert result == ["r/ai", "r/machinelearning", "r/artificial"]
        mock_reddit_client.search_subreddits.assert_not_called()

    def test_with_explicit_subreddits_whitespace(self, mock_reddit_client):
        """Test explicit subreddits with extra whitespace."""
        result = discover_subreddits(
            mock_reddit_client,
            niche="AI",
            subreddits=" r/ai , r/machinelearning , r/artificial ",
        )

        assert result == ["r/ai", "r/machinelearning", "r/artificial"]

    @patch("trendsleuth.cli.console")
    def test_discover_from_niche(self, mock_console, mock_reddit_client):
        """Test discovering subreddits from niche."""
        mock_reddit_client.search_subreddits.return_value = [
            "r/ai",
            "r/machinelearning",
            "r/artificial",
            "r/datascience",
            "r/deeplearning",
        ]

        result = discover_subreddits(mock_reddit_client, niche="AI", subreddits=None)

        assert result == [
            "r/ai",
            "r/machinelearning",
            "r/artificial",
            "r/datascience",
            "r/deeplearning",
        ]
        mock_reddit_client.search_subreddits.assert_called_once_with("AI", limit=5)
        mock_console.print.assert_called_once()

    @patch("trendsleuth.cli.console")
    def test_discover_no_results(self, mock_console, mock_reddit_client):
        """Test when no subreddits are found."""
        mock_reddit_client.search_subreddits.return_value = []

        with pytest.raises(CLIError, match="No subreddits found"):
            discover_subreddits(
                mock_reddit_client, niche="NonexistentNiche", subreddits=None
            )


class TestFetchSubredditData:
    """Tests for fetch_subreddit_data function."""

    @pytest.fixture
    def mock_reddit_client(self):
        """Create a mock Reddit client."""
        return Mock()

    def test_fetch_from_single_subreddit(self, mock_reddit_client):
        """Test fetching data from a single subreddit."""
        mock_reddit_client.get_subreddit_data.return_value = {
            "posts": [{"title": "Post 1"}, {"title": "Post 2"}],
            "comments": [{"body": "Comment 1"}, {"body": "Comment 2"}],
        }

        all_posts, all_comments, analyzed = fetch_subreddit_data(
            mock_reddit_client, ["r/test"], post_limit=10, comment_limit=20
        )

        assert len(all_posts) == 2
        assert len(all_comments) == 2
        assert analyzed == ["r/test"]
        mock_reddit_client.get_subreddit_data.assert_called_once_with(
            "r/test", post_limit=10, comment_limit=20
        )

    def test_fetch_from_multiple_subreddits(self, mock_reddit_client):
        """Test fetching data from multiple subreddits."""

        def mock_get_data(name, post_limit, comment_limit):
            if name == "r/ai":
                return {
                    "posts": [{"title": "AI Post"}],
                    "comments": [{"body": "AI Comment"}],
                }
            elif name == "r/ml":
                return {
                    "posts": [{"title": "ML Post"}],
                    "comments": [{"body": "ML Comment"}],
                }
            return {"posts": [], "comments": []}

        mock_reddit_client.get_subreddit_data.side_effect = mock_get_data

        all_posts, all_comments, analyzed = fetch_subreddit_data(
            mock_reddit_client, ["r/ai", "r/ml"], post_limit=10, comment_limit=20
        )

        assert len(all_posts) == 2
        assert len(all_comments) == 2
        assert analyzed == ["r/ai", "r/ml"]

    def test_fetch_with_empty_subreddit(self, mock_reddit_client):
        """Test fetching when one subreddit returns no data."""

        def mock_get_data(name, post_limit, comment_limit):
            if name == "r/ai":
                return {
                    "posts": [{"title": "AI Post"}],
                    "comments": [{"body": "AI Comment"}],
                }
            return {"posts": [], "comments": []}

        mock_reddit_client.get_subreddit_data.side_effect = mock_get_data

        all_posts, all_comments, analyzed = fetch_subreddit_data(
            mock_reddit_client, ["r/ai", "r/empty"], post_limit=10, comment_limit=20
        )

        assert len(all_posts) == 1
        assert len(all_comments) == 1
        assert analyzed == ["r/ai"]

    def test_fetch_no_data_from_any_subreddit(self, mock_reddit_client):
        """Test when no data is fetched from any subreddit."""
        mock_reddit_client.get_subreddit_data.return_value = {
            "posts": [],
            "comments": [],
        }

        with pytest.raises(CLIError, match="No data could be fetched"):
            fetch_subreddit_data(
                mock_reddit_client,
                ["r/empty1", "r/empty2"],
                post_limit=10,
                comment_limit=20,
            )


class TestAnalyzeContent:
    """Tests for analyze_content function."""

    @pytest.fixture
    def mock_analyzer(self):
        """Create a mock analyzer."""
        return Mock()

    @pytest.fixture
    def sample_posts(self):
        """Create sample posts."""
        return [{"title": f"Post {i}", "selftext": f"Content {i}"} for i in range(25)]

    @pytest.fixture
    def sample_comments(self):
        """Create sample comments."""
        return [{"body": f"Comment {i}"} for i in range(250)]

    @patch("trendsleuth.cli.console")
    def test_analyze_success(
        self, mock_console, mock_analyzer, sample_posts, sample_comments
    ):
        """Test successful analysis."""
        mock_analysis = TrendAnalysis(
            topics=["Topic 1", "Topic 2"],
            pain_points=["Pain 1"],
            questions=["Question 1"],
            sentiment="positive",
            summary="Test summary",
        )
        mock_analyzer.analyze_subreddit_data.return_value = mock_analysis

        result = analyze_content(
            mock_analyzer,
            niche="AI",
            posts=sample_posts,
            comments=sample_comments,
            include_evidence=False,
        )

        assert result == mock_analysis
        # Should limit to 20 posts and 200 comments
        mock_analyzer.analyze_subreddit_data.assert_called_once()
        call_args = mock_analyzer.analyze_subreddit_data.call_args
        assert len(call_args.kwargs["posts"]) == 20
        assert len(call_args.kwargs["comments"]) == 200

    @patch("trendsleuth.cli.console")
    def test_analyze_with_evidence(
        self, mock_console, mock_analyzer, sample_posts, sample_comments
    ):
        """Test analysis with evidence flag."""
        mock_analysis = TrendAnalysis(
            topics=["Topic 1"],
            pain_points=["Pain 1"],
            questions=["Question 1"],
            sentiment="positive",
            summary="Test summary",
            evidence=[],
        )
        mock_analyzer.analyze_subreddit_data.return_value = mock_analysis

        result = analyze_content(
            mock_analyzer,
            niche="AI",
            posts=sample_posts,
            comments=sample_comments,
            include_evidence=True,
        )

        assert result == mock_analysis
        call_args = mock_analyzer.analyze_subreddit_data.call_args
        assert call_args.kwargs["include_evidence"] is True

    @patch("trendsleuth.cli.console")
    def test_analyze_failure(
        self, mock_console, mock_analyzer, sample_posts, sample_comments
    ):
        """Test analysis failure."""
        mock_analyzer.analyze_subreddit_data.return_value = None

        with pytest.raises(CLIError, match="Failed to analyze the data"):
            analyze_content(
                mock_analyzer, niche="AI", posts=sample_posts, comments=sample_comments
            )


class TestFormatOutput:
    """Tests for format_output function."""

    @pytest.fixture
    def sample_analysis(self):
        """Create a sample analysis."""
        return TrendAnalysis(
            topics=["Topic 1", "Topic 2"],
            pain_points=["Pain 1"],
            questions=["Question 1"],
            sentiment="positive",
            summary="Test summary",
        )

    @patch("trendsleuth.cli.format_markdown")
    def test_format_markdown(self, mock_format_md, sample_analysis):
        """Test formatting as markdown."""
        mock_format_md.return_value = "# Markdown output"

        result = format_output(sample_analysis, "markdown", "AI")

        assert result == "# Markdown output"
        mock_format_md.assert_called_once_with(
            subreddit="AI", analysis=sample_analysis, token_usage=None, cost=None
        )

    @patch("trendsleuth.cli.format_json")
    def test_format_json(self, mock_format_json, sample_analysis):
        """Test formatting as JSON."""
        mock_format_json.return_value = '{"result": "json"}'

        result = format_output(sample_analysis, "json", "AI")

        assert result == '{"result": "json"}'
        mock_format_json.assert_called_once_with(
            subreddit="AI", analysis=sample_analysis, token_usage=None, cost=None
        )

    def test_format_unsupported(self, sample_analysis):
        """Test with unsupported format."""
        with pytest.raises(ValueError, match="Unsupported output format"):
            format_output(sample_analysis, "xml", "AI")


class TestWriteOutput:
    """Tests for write_output function."""

    @patch("trendsleuth.cli.console")
    def test_write_to_stdout(self, mock_console):
        """Test writing to stdout."""
        content = "Test output content"

        write_output(content, output_file=None)

        assert mock_console.print.call_count == 2
        mock_console.print.assert_called_with(content)

    @patch("trendsleuth.cli.console")
    def test_write_to_file(self, mock_console, tmp_path):
        """Test writing to a file."""
        content = "Test output content"
        output_file = tmp_path / "output.txt"

        write_output(content, str(output_file))

        assert output_file.exists()
        assert output_file.read_text() == content
        mock_console.print.assert_called_once()


class TestPrintSummary:
    """Tests for print_summary function."""

    @pytest.fixture
    def analysis_context(self):
        """Create a sample analysis context."""
        analysis = TrendAnalysis(
            topics=["Topic 1", "Topic 2", "Topic 3"],
            pain_points=["Pain 1", "Pain 2"],
            questions=["Question 1"],
            sentiment="positive",
            summary="Test summary",
        )
        return AnalysisContext(
            niche="AI",
            subreddit_list=["r/ai", "r/ml"],
            all_posts=[{"title": "Post 1"}],
            all_comments=[{"body": "Comment 1"}, {"body": "Comment 2"}],
            analyzed_subreddits=["r/ai", "r/ml"],
            analysis=analysis,
        )

    @patch("trendsleuth.cli.console")
    def test_print_summary_basic(self, mock_console, analysis_context):
        """Test printing basic summary."""
        print_summary(analysis_context, verbose=False)

        assert mock_console.print.call_count == 1

    @patch("trendsleuth.cli.console")
    def test_print_summary_verbose(self, mock_console, analysis_context):
        """Test printing verbose summary."""
        print_summary(analysis_context, verbose=True)

        # Verbose mode prints: newline, table, and final panel (3 calls)
        assert mock_console.print.call_count == 3

    @patch("trendsleuth.cli.console")
    def test_print_summary_no_analysis(self, mock_console):
        """Test printing summary when analysis is None."""
        ctx = AnalysisContext(
            niche="AI",
            subreddit_list=["r/ai"],
            all_posts=[],
            all_comments=[],
            analyzed_subreddits=[],
            analysis=None,
        )

        print_summary(ctx, verbose=False)

        mock_console.print.assert_not_called()


class TestRunAnalysisPipeline:
    """Tests for run_analysis_pipeline function."""

    @pytest.fixture
    def mock_reddit_config(self):
        """Create mock Reddit config."""
        return RedditConfig(
            client_id="test_id", client_secret="test_secret", user_agent="test_agent"
        )

    @pytest.fixture
    def mock_openai_config(self):
        """Create mock OpenAI config."""
        return OpenAIConfig(api_key="test_key")

    @patch("trendsleuth.cli.RedditClient")
    @patch("trendsleuth.cli.Analyzer")
    def test_run_pipeline_basic(
        self,
        mock_analyzer_class,
        mock_reddit_class,
        mock_reddit_config,
        mock_openai_config,
    ):
        """Test running basic analysis pipeline."""
        # Mock Reddit client
        mock_reddit = Mock()
        mock_reddit.search_subreddits.return_value = ["r/ai"]
        mock_reddit.get_subreddit_data.return_value = {
            "posts": [{"title": "Post 1"}],
            "comments": [{"body": "Comment 1"}],
        }
        mock_reddit_class.return_value = mock_reddit

        # Mock Analyzer
        mock_analyzer = Mock()
        mock_analysis = TrendAnalysis(
            topics=["Topic 1"],
            pain_points=["Pain 1"],
            questions=["Question 1"],
            sentiment="positive",
            summary="Test summary",
        )
        mock_analyzer.analyze_subreddit_data.return_value = mock_analysis
        mock_analyzer_class.return_value = mock_analyzer

        result = run_analysis_pipeline(
            reddit_config=mock_reddit_config,
            openai_config=mock_openai_config,
            niche="AI",
            subreddits=None,
            post_limit=10,
            comment_limit=20,
        )

        assert result.niche == "AI"
        assert result.analysis == mock_analysis
        assert len(result.all_posts) == 1
        assert len(result.all_comments) == 1

    @patch("trendsleuth.cli.RedditClient")
    @patch("trendsleuth.cli.Analyzer")
    def test_run_pipeline_with_explicit_subreddits(
        self,
        mock_analyzer_class,
        mock_reddit_class,
        mock_reddit_config,
        mock_openai_config,
    ):
        """Test pipeline with explicit subreddits."""
        mock_reddit = Mock()
        mock_reddit.get_subreddit_data.return_value = {
            "posts": [{"title": "Post 1"}],
            "comments": [{"body": "Comment 1"}],
        }
        mock_reddit_class.return_value = mock_reddit

        mock_analyzer = Mock()
        mock_analysis = TrendAnalysis(
            topics=["Topic 1"],
            pain_points=["Pain 1"],
            questions=["Question 1"],
            sentiment="positive",
            summary="Test summary",
        )
        mock_analyzer.analyze_subreddit_data.return_value = mock_analysis
        mock_analyzer_class.return_value = mock_analyzer

        result = run_analysis_pipeline(
            reddit_config=mock_reddit_config,
            openai_config=mock_openai_config,
            niche="AI",
            subreddits="r/ai,r/ml",
            post_limit=10,
            comment_limit=20,
        )

        assert result.niche == "AI"
        assert len(result.subreddit_list) == 2
        mock_reddit.search_subreddits.assert_not_called()


class TestAnalyzeCommand:
    """Tests for the analyze command."""

    @patch("trendsleuth.cli.validate_configuration")
    @patch("trendsleuth.cli.run_analysis_pipeline")
    @patch("trendsleuth.cli.get_config")
    def test_analyze_command_basic(self, mock_get_config, mock_pipeline, mock_validate):
        """Test basic analyze command."""
        mock_validate.return_value = True

        mock_reddit_config = RedditConfig(
            client_id="test_id", client_secret="test_secret", user_agent="test_agent"
        )
        mock_openai_config = OpenAIConfig(api_key="test_key")
        mock_get_config.return_value = (
            mock_reddit_config,
            mock_openai_config,
            None,
            None,
        )

        mock_analysis = TrendAnalysis(
            topics=["Topic 1"],
            pain_points=["Pain 1"],
            questions=["Question 1"],
            sentiment="positive",
            summary="Test summary",
        )
        mock_ctx = AnalysisContext(
            niche="AI",
            subreddit_list=["r/ai"],
            all_posts=[],
            all_comments=[],
            analyzed_subreddits=["r/ai"],
            analysis=mock_analysis,
        )
        mock_pipeline.return_value = mock_ctx

        result = runner.invoke(app, ["analyze", "AI"])

        assert result.exit_code == 0

    @patch("trendsleuth.cli.validate_configuration")
    def test_analyze_command_invalid_config(self, mock_validate):
        """Test analyze command with invalid configuration."""
        mock_validate.return_value = False

        result = runner.invoke(app, ["analyze", "AI"])

        assert result.exit_code == 1

    @patch("trendsleuth.cli.validate_configuration")
    @patch("trendsleuth.cli.get_config")
    def test_analyze_command_invalid_format(self, mock_get_config, mock_validate):
        """Test analyze command with invalid format."""
        mock_validate.return_value = True
        mock_get_config.return_value = (Mock(), Mock(), None, None)

        result = runner.invoke(app, ["analyze", "AI", "--format", "xml"])

        assert result.exit_code == 1

    @patch("trendsleuth.cli.validate_configuration")
    @patch("trendsleuth.cli.run_analysis_pipeline")
    @patch("trendsleuth.cli.get_config")
    def test_analyze_command_with_output_file(
        self, mock_get_config, mock_pipeline, mock_validate, tmp_path
    ):
        """Test analyze command with output file."""
        mock_validate.return_value = True

        mock_reddit_config = RedditConfig(
            client_id="test_id", client_secret="test_secret", user_agent="test_agent"
        )
        mock_openai_config = OpenAIConfig(api_key="test_key")
        mock_get_config.return_value = (
            mock_reddit_config,
            mock_openai_config,
            None,
            None,
        )

        mock_analysis = TrendAnalysis(
            topics=["Topic 1"],
            pain_points=["Pain 1"],
            questions=["Question 1"],
            sentiment="positive",
            summary="Test summary",
        )
        mock_ctx = AnalysisContext(
            niche="AI",
            subreddit_list=["r/ai"],
            all_posts=[],
            all_comments=[],
            analyzed_subreddits=["r/ai"],
            analysis=mock_analysis,
        )
        mock_pipeline.return_value = mock_ctx

        output_file = tmp_path / "output.md"
        result = runner.invoke(app, ["analyze", "AI", "--output", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()


class TestNichesCommand:
    """Tests for the niches command."""

    @patch("trendsleuth.cli.validate_env_vars")
    @patch("trendsleuth.cli.get_config")
    @patch("trendsleuth.cli.Analyzer")
    def test_niches_command_basic(
        self, mock_analyzer_class, mock_get_config, mock_validate
    ):
        """Test basic niches command."""
        mock_validate.return_value = []
        mock_get_config.return_value = (None, OpenAIConfig(api_key="test"), None, None)

        mock_analyzer = Mock()
        mock_analyzer.generate_niches.return_value = ["Niche 1", "Niche 2", "Niche 3"]
        mock_analyzer_class.return_value = mock_analyzer

        result = runner.invoke(app, ["niches", "--theme", "technology"])

        assert result.exit_code == 0
        assert "Niche 1" in result.stdout

    @patch("trendsleuth.cli.validate_env_vars")
    @patch("trendsleuth.cli.get_config")
    @patch("trendsleuth.cli.Analyzer")
    def test_niches_command_json_output(
        self, mock_analyzer_class, mock_get_config, mock_validate
    ):
        """Test niches command with JSON output."""
        mock_validate.return_value = []
        mock_get_config.return_value = (None, OpenAIConfig(api_key="test"), None, None)

        mock_analyzer = Mock()
        mock_analyzer.generate_niches.return_value = ["Niche 1", "Niche 2"]
        mock_analyzer_class.return_value = mock_analyzer

        result = runner.invoke(app, ["niches", "--theme", "technology", "--json"])

        assert result.exit_code == 0
        output_data = json.loads(result.stdout)
        assert len(output_data) == 2

    @patch("trendsleuth.cli.validate_env_vars")
    def test_niches_command_missing_openai(self, mock_validate):
        """Test niches command with missing OpenAI config."""
        mock_validate.return_value = ["OPENAI_API_KEY"]

        result = runner.invoke(app, ["niches", "--theme", "technology"])

        assert result.exit_code == 1

    @patch("trendsleuth.cli.validate_env_vars")
    @patch("trendsleuth.cli.get_config")
    @patch("trendsleuth.cli.Analyzer")
    def test_niches_command_with_count(
        self, mock_analyzer_class, mock_get_config, mock_validate
    ):
        """Test niches command with custom count."""
        mock_validate.return_value = []
        mock_get_config.return_value = (None, OpenAIConfig(api_key="test"), None, None)

        mock_analyzer = Mock()
        mock_analyzer.generate_niches.return_value = ["Niche 1", "Niche 2", "Niche 3"]
        mock_analyzer_class.return_value = mock_analyzer

        result = runner.invoke(app, ["niches", "--theme", "technology", "--count", "3"])

        assert result.exit_code == 0
        mock_analyzer.generate_niches.assert_called_once_with(
            theme="technology", count=3
        )


class TestIdeasCommand:
    """Tests for the ideas command."""

    @patch("trendsleuth.cli.validate_env_vars")
    @patch("trendsleuth.cli.get_config")
    @patch("trendsleuth.cli.load_analysis_file")
    @patch("trendsleuth.cli.generate_ideas")
    @patch("trendsleuth.cli.format_ideas_as_markdown")
    def test_ideas_command_basic(
        self,
        mock_format,
        mock_generate,
        mock_load,
        mock_get_config,
        mock_validate,
        tmp_path,
    ):
        """Test basic ideas command."""
        mock_validate.return_value = []
        mock_get_config.return_value = (None, OpenAIConfig(api_key="test"), None, None)

        # Create a dummy analysis file
        analysis_file = tmp_path / "analysis.json"
        analysis_file.write_text(
            json.dumps(
                {
                    "subreddit": "r/ai",
                    "analysis": {
                        "summary": "Test",
                        "topics": ["Topic 1"],
                        "pain_points": ["Pain 1"],
                        "questions": ["Question 1"],
                    },
                }
            )
        )

        from trendsleuth.ideas import AnalysisSignals

        mock_load.return_value = AnalysisSignals(
            niche="ai",
            summary="Test",
            topics=["Topic 1"],
            pain_points=["Pain 1"],
            questions=["Question 1"],
        )

        mock_generate.return_value = [{"title": "Business Idea 1"}]
        mock_format.return_value = "# Business Idea 1"

        result = runner.invoke(
            app, ["ideas", "--input", str(analysis_file), "--type", "business"]
        )

        assert result.exit_code == 0

    @patch("trendsleuth.cli.validate_env_vars")
    def test_ideas_command_missing_openai(self, mock_validate):
        """Test ideas command with missing OpenAI config."""
        mock_validate.return_value = ["OPENAI_API_KEY"]

        result = runner.invoke(
            app, ["ideas", "--input", "analysis.json", "--type", "business"]
        )

        assert result.exit_code == 1

    @patch("trendsleuth.cli.validate_env_vars")
    @patch("trendsleuth.cli.get_config")
    def test_ideas_command_invalid_type(self, mock_get_config, mock_validate):
        """Test ideas command with invalid idea type."""
        mock_validate.return_value = []
        mock_get_config.return_value = (None, OpenAIConfig(api_key="test"), None, None)

        result = runner.invoke(
            app, ["ideas", "--input", "analysis.json", "--type", "invalid"]
        )

        assert result.exit_code == 1

    @patch("trendsleuth.cli.validate_env_vars")
    @patch("trendsleuth.cli.get_config")
    def test_ideas_command_invalid_format(self, mock_get_config, mock_validate):
        """Test ideas command with invalid format."""
        mock_validate.return_value = []
        mock_get_config.return_value = (None, OpenAIConfig(api_key="test"), None, None)

        result = runner.invoke(
            app,
            [
                "ideas",
                "--input",
                "analysis.json",
                "--type",
                "business",
                "--format",
                "xml",
            ],
        )

        assert result.exit_code == 1

    @patch("trendsleuth.cli.validate_env_vars")
    @patch("trendsleuth.cli.get_config")
    @patch("trendsleuth.cli.load_analysis_file")
    @patch("trendsleuth.cli.generate_ideas")
    def test_ideas_command_json_output(
        self, mock_generate, mock_load, mock_get_config, mock_validate, tmp_path
    ):
        """Test ideas command with JSON output."""
        mock_validate.return_value = []
        mock_get_config.return_value = (None, OpenAIConfig(api_key="test"), None, None)

        analysis_file = tmp_path / "analysis.json"
        analysis_file.write_text(
            json.dumps(
                {
                    "subreddit": "r/ai",
                    "analysis": {
                        "summary": "Test",
                        "topics": ["Topic 1"],
                        "pain_points": ["Pain 1"],
                        "questions": ["Question 1"],
                    },
                }
            )
        )

        from trendsleuth.ideas import AnalysisSignals

        mock_load.return_value = AnalysisSignals(
            niche="ai",
            summary="Test",
            topics=["Topic 1"],
            pain_points=["Pain 1"],
            questions=["Question 1"],
        )

        mock_generate.return_value = [
            {"title": "Business Idea 1", "description": "Description"}
        ]

        result = runner.invoke(
            app,
            [
                "ideas",
                "--input",
                str(analysis_file),
                "--type",
                "business",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0
        # Should contain valid JSON
        assert '"title"' in result.stdout


class TestConfigCommand:
    """Tests for the config command."""

    @patch("trendsleuth.cli.get_config")
    def test_config_show_command(self, mock_get_config):
        """Test config --show command."""
        mock_reddit_config = RedditConfig(
            client_id="test_client_id_12345",
            client_secret="test_secret",
            user_agent="TrendSleuth/1.0",
        )
        mock_openai_config = OpenAIConfig(
            api_key="test_api_key_67890", model="gpt-4o-mini"
        )
        mock_get_config.return_value = (
            mock_reddit_config,
            mock_openai_config,
            None,
            None,
        )

        result = runner.invoke(app, ["config", "--show"])

        assert result.exit_code == 0
        assert "Current Configuration" in result.stdout
        assert "gpt-4o-mini" in result.stdout


class TestAnalysisContext:
    """Tests for AnalysisContext dataclass."""

    def test_context_creation(self):
        """Test creating an AnalysisContext."""
        ctx = AnalysisContext(
            niche="AI",
            subreddit_list=["r/ai"],
            all_posts=[],
            all_comments=[],
            analyzed_subreddits=["r/ai"],
        )

        assert ctx.niche == "AI"
        assert ctx.subreddit_list == ["r/ai"]
        assert ctx.analysis is None

    def test_context_with_analysis(self):
        """Test AnalysisContext with analysis results."""
        analysis = TrendAnalysis(
            topics=["Topic 1"],
            pain_points=["Pain 1"],
            questions=["Question 1"],
            sentiment="positive",
            summary="Test summary",
        )

        ctx = AnalysisContext(
            niche="AI",
            subreddit_list=["r/ai"],
            all_posts=[],
            all_comments=[],
            analyzed_subreddits=["r/ai"],
            analysis=analysis,
        )

        assert ctx.analysis == analysis


class TestCLIError:
    """Tests for CLIError exception."""

    def test_cli_error_creation(self):
        """Test creating a CLIError."""
        error = CLIError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
