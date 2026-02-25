# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
