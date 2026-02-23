# TrendSleuth

> **Reddit trend analysis for content creators**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

TrendSleuth helps content creators discover trending topics, pain points, and questions on Reddit by analyzing subreddits with AI.

## Features

- 🔍 **Auto-discover subreddits** - Find relevant communities for your niche
- 📊 **AI-powered analysis** - Extract topics, pain points, and questions
- 📝 **Markdown & JSON output** - Get results in your preferred format
- 💰 **Cost tracking** - See token usage and estimated API costs
- 🚀 **Fast & efficient** - Process hundreds of posts and comments quickly
- 📺 **Rich terminal UI** - Beautiful progress indicators and results

## Installation

### Prerequisites

- Python 3.12 or higher
- Reddit API credentials
- OpenAI API key

### Setup

1. **Install TrendSleuth:**

```bash
# Using pip
pip install trendsleuth

# Or using uv (recommended)
uv tool install trendsleuth
```

2. **Configure API Keys:**

```bash
# Set environment variables
export REDDIT_CLIENT_ID="your_reddit_client_id"
export REDDIT_CLIENT_SECRET="your_reddit_client_secret"
export REDDIT_USER_AGENT="TrendSleuth/0.1.0"
export OPENAI_API_KEY="your_openai_api_key"
```

**Get API Credentials:**
- **Reddit:** Create an app at [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
- **OpenAI:** Get an API key at [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

## Usage

### Basic Analysis

```bash
trendsleuth analyze "ai agents"
```

### Advanced Options

```bash
# Analyze specific subreddits
trendsleuth analyze "machine learning" \
  --subreddits r/MachineLearning,r/ArtificialIntel,r/learnmachinelearning

# Save results to a file
trendsleuth analyze "content creation" \
  --output report.md

# Get JSON output
trendsleuth analyze "photography" \
  --format json

# Adjust analysis depth
trendsleuth analyze "gaming" \
  --limit 100
```

### Full Command Reference

```
Usage: trendsleuth analyze [OPTIONS] NICHE

Arguments:
  NICHE              The niche or topic to analyze

Options:
  -s, --subreddits TEXT     Comma-separated list of subreddits
  -o, --output PATH         Output file path
  -l, --limit INTEGER       Maximum posts to analyze (default: 50)
  -f, --format [markdown|json]  Output format (default: markdown)
  --model TEXT              OpenAI model (default: gpt-4o-mini)
  -v, --verbose             Enable verbose output
  --help                    Show this message and exit
```

### Configuration Commands

```bash
# Show current configuration
trendsleuth config --show
```

## Output Example

```
# Trend Analysis: ai agents

**Generated at:** 2026-02-23 15:30:45

## Summary

The AI agents community shows strong enthusiasm for autonomous agents, with 
significant focus on LLM integration and practical applications across various 
industries. Users express excitement about rapid advancements while concerned 
about accessibility and implementation complexity.

## Trending Topics

1. Autonomous AI agents
2. LLM-powered workflows
3. Multi-agent systems
4. AI coding assistants
5. Customer service automation
6. Creative AI tools
7. AI agent frameworks
8. Agent orchestration
9. AI safety and alignment
10. Enterprise AI adoption

## Pain Points

1. High computational costs
2. Complex setup and configuration
3. Lack of comprehensive documentation
4. Integration with existing tools
5. Model selection confusion
6. Security concerns
7. Cost management

## Questions & Curiosities

1. How to get started with AI agents?
2. What are the best frameworks for building agents?
3. How do I choose the right LLM for my agent?
4. What are best practices for agent orchestration?
5. How can I reduce costs while maintaining performance?
6. What security measures are essential?
7. Are there enterprise-grade AI agent solutions?

## Metrics

- **Total tokens used:** 12,345
- **Estimated cost:** $0.0315
```

## Development

### Setup for Contributors

```bash
# Clone the repository
git clone https://github.com/lukemaxwell/trendsleuth.git
cd trendsleuth

# Install with uv
uv sync

# Activate the virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install in development mode
uv pip install -e .
```

### Running Tests

```bash
uv run pytest
```

### Code Quality

```bash
# Linting
uv run ruff check .

# Type checking (if configured)
uv run mypy .
```

## Project Structure

```
trendsleuth/
├── src/trendsleuth/
│   ├── __init__.py
│   ├── cli.py          # CLI entry point
│   ├── config.py       # Configuration management
│   ├── reddit.py       # Reddit API client
│   ├── analyzer.py     # LLM-based analysis
│   └── formatter.py    # Output formatting
├── tests/
│   ├── test_reddit.py
│   ├── test_analyzer.py
│   └── test_formatter.py
├── examples/
│   └── sample-output.md
├── pyproject.toml
└── README.md
```

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgments

- Built with [Typer](https://github.com/tiangolo/typer) for the CLI
- Powered by [PRAW](https://praw.readthedocs.io/) for Reddit API access
- AI analysis via [LangChain](https://python.langchain.com/) + OpenAI

---

<div align="center">
  <p>Happy analyzing! 📊🤖</p>
</div>
