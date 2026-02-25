# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Accurate cost estimation** for all OpenAI models (not just gpt-4o-mini)
- New `pricing.py` module with comprehensive pricing data for all OpenAI models
- New `token_tracker.py` module for tracking LangChain token usage
- Token usage and cost display in verbose mode and completion messages
- Cost information included in Markdown and JSON output
- Warning log when unknown model uses fallback pricing
- 14 new tests for pricing module

### Changed
- `Analyzer.analyze_subreddit_data()` now returns tuple: `(analysis, token_usage, cost)`
- CLI displays accurate costs based on selected model
- Cost estimates use actual OpenAI pricing (as of Feb 2026)

### Fixed
- Cost estimation now reflects the actual model selected by user
- Previously all cost estimates used gpt-4o-mini pricing regardless of model

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
