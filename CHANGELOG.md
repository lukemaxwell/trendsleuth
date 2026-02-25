# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.4] - 2026-02-25

### Fixed
- Screenshot image in README now uses full GitHub raw URL for PyPI compatibility
- PyPI package page now displays the screenshot correctly

## [0.1.3] - 2026-02-25

### Added
- **Accurate cost estimation** for all OpenAI models (not just gpt-4o-mini)
- New `pricing.py` module with comprehensive pricing data for 36+ OpenAI models
- New `token_tracker.py` module for real-time LangChain token usage tracking
- Token usage (input/output/total) displayed in verbose mode and completion messages
- Cost information included in both Markdown and JSON output formats
- Fallback pricing for unknown or future OpenAI models
- Warning log when unknown model uses fallback pricing
- 14 new comprehensive tests for pricing module
- GitHub Actions workflow for automated PyPI publishing
- Complete release documentation (`RELEASE_PROCESS.md`, `PYPI_SETUP.md`)

### Changed
- `Analyzer.analyze_subreddit_data()` now returns tuple: `(analysis, token_usage, cost)`
- `Analyzer.estimate_cost()` now uses actual model pricing instead of hardcoded gpt-4o-mini rates
- CLI displays accurate costs based on user's selected model (e.g., `--model gpt-4o`)
- Cost estimates use real OpenAI API pricing (as of February 2026)
- All analyzer and CLI tests updated to handle new tuple return format

### Fixed
- **Critical:** Cost estimation now correctly reflects the actual model selected by user
- Previously all cost estimates incorrectly used gpt-4o-mini pricing regardless of `--model` parameter
- This could result in significant cost underestimation (e.g., gpt-4o is ~17x more expensive than gpt-4o-mini)

### Technical
- Added `TokenUsageTracker` callback handler for LangChain
- Added pricing data structure with per-1M-token costs for input/output
- Enhanced `AnalysisContext` to store token_usage and cost
- Updated `format_output()` to include cost metrics in output
- Updated `print_summary()` to display token usage in verbose mode
- All 119 tests passing with new token tracking system

## [0.1.2] - 2026-02-26

### Added
- Initial PyPI release with all core features

## [0.1.1] - 2026-02-25

### Fixed
- Fixed screenshot image not displaying on PyPI (now uses GitHub raw URL)
- Fixed typo in image alt text ("Anaylsis" → "Analysis")

### Added
- PyPI version badge in README

## [0.1.0] - 2026-02-25

### Added
- Initial release of TrendSleuth CLI
- Reddit trend analysis with auto-discovered subreddits
- LLM-powered extraction of topics, pain points, and questions
- Evidence collection with verbatim quotes from Reddit and web sources
- Web evidence gathering using Brave Search API
- Niche generation command for discovering specific niches within themes
- Ideas generation command to transform analysis into business, app, or content ideas
- Support for both Markdown and JSON output formats
- Rich terminal output with progress indicators and beautiful formatting
- Cost tracking for OpenAI API usage
- Comprehensive test suite with 111 tests
- Type hints throughout the codebase
- Detailed documentation and examples

### Features
- **analyze** command: Analyze Reddit trends for any niche
- **niches** command: Generate niche ideas for a given theme
- **ideas** command: Transform analysis into actionable ideas
- **config** command: View current configuration
- Support for custom subreddit lists
- Rate limiting for Brave Search API
- Advanced web scraping with curl-cffi for anti-bot bypass
- Flexible configuration via environment variables or .env file

### Technical
- Built with Typer for CLI framework
- Uses PRAW for Reddit API access
- LangChain + OpenAI for AI analysis
- Rich library for beautiful terminal output
- Pydantic for data validation
- curl-cffi for robust web scraping
- Full type annotations with mypy support
