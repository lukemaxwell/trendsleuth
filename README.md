# TrendSleuth

> **From Reddit signals to validated ideas**

[![PyPI version](https://badge.fury.io/py/trendsleuth.svg)](https://badge.fury.io/py/trendsleuth)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![codecov](https://codecov.io/gh/lukemaxwell/trendsleuth/graph/badge.svg)](https://codecov.io/gh/lukemaxwell/trendsleuth)

TrendSleuth analyzes Reddit conversations to uncover emerging trends, pain points, and unanswered questions and turns those insights into actionable content, product, and business ideas.

![Analysis screenshot](https://raw.githubusercontent.com/lukemaxwell/trendsleuth/main/trendsleuth-analysis.png)

## Features

- 🔍 **Auto-discover subreddits** - Find relevant communities for your niche
- 📊 **AI-powered analysis** - Extract topics, pain points, and questions
- 🔗 **Evidence collection** - Gather verbatim quotes from Reddit and web sources
- 💡 **Niche generation** - Generate specific niche ideas for any theme
- 🎯 **Idea generation** - Transform analysis into business, app, or content ideas
- 📝 **Markdown & JSON output** - Get results in your preferred format
- 🌐 **Web evidence** - Search the web using Brave Search API for additional insights
- 💰 **Cost tracking** - See token usage and estimated API costs
- 🚀 **Fast & efficient** - Process hundreds of posts and comments quickly
- 📺 **Rich terminal UI** - Beautiful progress indicators and results

## Installation

### Prerequisites

- Python 3.12 or higher
- Reddit API credentials
- OpenAI API key

### Quick Install (from PyPI)

```bash
# Using pip
pip install trendsleuth

# Or using pipx (recommended for CLI tools)
pipx install trendsleuth

# Or using uv
uv tool install trendsleuth
```

### Install from Source

If you want the latest development version:

```bash
# Clone the repository
git clone https://github.com/lukemaxwell/trendsleuth.git
cd trendsleuth

# Install with uv (recommended)
uv sync

# Activate the virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install in development mode
uv pip install -e .
```

**Alternative: Install from source with pip**

```bash
# Clone the repository
git clone https://github.com/lukemaxwell/trendsleuth.git
cd trendsleuth

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -e .
```

### Configure API Keys

```bash
# Set environment variables
export REDDIT_CLIENT_ID="your_reddit_client_id"
export REDDIT_CLIENT_SECRET="your_reddit_client_secret"
export REDDIT_USER_AGENT="TrendSleuth/0.1.0"
export OPENAI_API_KEY="your_openai_api_key"

# Optional: For web evidence gathering
export BRAVE_API_KEY="your_brave_api_key"
```

**Get API Credentials:**
- **Reddit:** Create an app at [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
- **OpenAI:** Get an API key at [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Brave Search (optional):** Sign up at [https://brave.com/search/api/](https://brave.com/search/api/)

## Usage

### Analyze Trends

Basic trend analysis:
```bash
trendsleuth analyze "ai agents"
```

With evidence from Reddit:
```bash
trendsleuth analyze "ai agents" --include-evidence
```

With web evidence from Brave Search:
```bash
trendsleuth analyze "ai agents" --include-evidence --include-web
```

### Advanced Analysis Options

```bash
# Analyze specific subreddits
trendsleuth analyze "machine learning" \
  --subreddits r/MachineLearning,r/ArtificialIntel,r/learnmachinelearning

# Save results to a file
trendsleuth analyze "content creation" \
  --output report.md

# Get JSON output with evidence
trendsleuth analyze "photography" \
  --format json \
  --include-evidence

# Adjust analysis depth and web evidence
trendsleuth analyze "gaming" \
  --limit 100 \
  --include-web \
  --web-evidence-limit 20 \
  --web-results-per-query 10
```

### Generate Niche Ideas

Generate niche ideas for a theme:
```bash
trendsleuth niches --theme "productivity"
```

With custom count:
```bash
trendsleuth niches --theme "fitness" --count 25
```

JSON output:
```bash
trendsleuth niches --theme "travel" --json
```

### Generate Ideas from Analysis

Transform TrendSleuth analysis into actionable business, app, or content ideas:

```bash
# Generate business ideas from analysis
trendsleuth ideas --input analysis.json --type business --count 3

# Generate app ideas
trendsleuth ideas --input analysis.md --type app --count 5

# Generate content ideas
trendsleuth ideas --input report.json --type content --count 10

# Get JSON output
trendsleuth ideas --input analysis.json --type business --format json
```

Idea types:
- **business**: Complete business concepts with monetization, validation, etc.
- **app**: Product/MVP ideas with features and scope
- **content**: High-engagement content ideas for social media

### Full Command Reference

#### Analyze Command

```
Usage: trendsleuth analyze [OPTIONS] NICHE

Arguments:
  NICHE              The niche or topic to analyze

Options:
  -s, --subreddits TEXT          Comma-separated list of subreddits
  -o, --output PATH              Output file path
  -l, --limit INTEGER            Maximum posts to analyze (default: 50)
  -f, --format [markdown|json]   Output format (default: markdown)
  --model TEXT                   OpenAI model (default: gpt-4o-mini)
  --include-evidence             Include evidence with verbatim quotes
  --include-web                  Gather web evidence using Brave Search
  --web-evidence-limit INTEGER   Max web evidence items (default: 15)
  --web-results-per-query INT    Brave results per query (default: 5)
  --web-rate-limit-rps FLOAT     Brave API rate limit RPS (default: 1.0)
  -v, --verbose                  Enable verbose output
  --help                         Show this message and exit
```

#### Niches Command

```
Usage: trendsleuth niches [OPTIONS]

Options:
  --theme TEXT         Topic or domain to generate niches for (required)
  --count INTEGER      Number of niches to generate (default: 15)
  --json               Output as JSON array
  --model TEXT         OpenAI model (default: gpt-4o-mini)
  --help               Show this message and exit
```

#### Ideas Command
It is highly recommended to use the best models available for idea generation, e.g. gpt-5.2.

```
Usage: trendsleuth ideas [OPTIONS]

Options:
  --input TEXT         Path to TrendSleuth analysis file (JSON or Markdown) (required)
  --type TEXT          Type of ideas: business, app, or content (default: business)
  --count INTEGER      Number of ideas to generate (default: 1)
  --format TEXT        Output format: md or json (default: md)
  --model TEXT         OpenAI model (default: gpt-4o-mini)
  --help               Show this message and exit
```

### Configuration Commands

```bash
# Show current configuration
trendsleuth config --show
```

## Output Examples

### Analyze Command Output

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

## Evidence (Recent)

- [2024-02-20] [REDDIT] "The setup process is way too complicated for beginners..." — https://reddit.com/r/ai/...
- [2024-02-19] [WEB] "Cost management is a huge issue when running multiple agents..." — https://example.com/...
- [unknown] [WEB] "Documentation is severely lacking for most frameworks." — https://example.com/...

## Metrics

- **Total tokens used:** 12,345
- **Estimated cost:** $0.0315
```

### Niches Command Output

```bash
$ trendsleuth niches --theme "productivity" --count 5
```

```
1. AI-powered meeting summarization tools
2. Focus mode apps for remote workers
3. Habit tracking with behavioral psychology
4. Time blocking calendars for ADHD users
5. Automated workflow builders for solopreneurs
```

With JSON output:
```bash
$ trendsleuth niches --theme "productivity" --count 3 --json
```

```json
[
  "AI-powered meeting summarization tools",
  "Focus mode apps for remote workers",
  "Habit tracking with behavioral psychology"
]
```

### Ideas Command Output

```bash
$ trendsleuth ideas --input analysis.json --type business --count 2
```

```markdown
## Idea 1

**AgentStack Pro**

_All-in-one platform for deploying and managing AI agents at scale_

**Target Customer:** Mid-size companies (50-500 employees) wanting to implement AI agents without hiring specialized ML engineers

**Core Pain:** High computational costs and complex setup make AI agents inaccessible to most businesses

**Product:** Managed platform that handles infrastructure, provides pre-built agent templates, and includes monitoring/cost optimization tools

**Why Existing Solutions Fail:** Current solutions require deep technical expertise and force companies to build everything from scratch

**Monetization:** Usage-based pricing with enterprise support tiers

**Pricing:** Free tier (1 agent, 10k messages/month), Pro at $99/month (5 agents, 100k messages), Enterprise custom pricing

**Validation Strategy:** Launch with 3 pre-built agent templates (customer support, sales assistant, content writer). Partner with 5 beta companies for case studies. Success metric: 50+ signups in first month with 20% converting to paid.

## Idea 2

**Agent Cost Optimizer**

_SaaS tool that automatically reduces AI agent operational costs by 40-60%_

**Target Customer:** Companies already running AI agents who are struggling with unpredictable and high costs

**Core Pain:** Cost management is a huge challenge when running multiple agents with different LLM providers

**Product:** Dashboard that analyzes agent usage patterns, recommends model optimizations, implements caching strategies, and auto-routes queries to most cost-effective models

**Why Existing Solutions Fail:** No dedicated tools exist for AI agent cost optimization - companies do this manually and miss significant savings

**Monetization:** Revenue share model - we take 20% of the savings we generate

**Pricing:** Free audit, then 20% of monthly savings (minimum $299/month)

**Validation Strategy:** Offer free cost audits to 20 companies from r/LocalLLaMA and r/ArtificialIntelligence. Show concrete savings projections. Success metric: 5+ companies sign LOIs.
```

App ideas output:
```bash
$ trendsleuth ideas --input analysis.md --type app --count 1
```

```markdown
## Idea 1

**AgentLab**

**Target User:** Developers and technical founders who want to experiment with AI agents without infrastructure overhead

**Problem:** Setting up AI agent development environments is complex, time-consuming, and expensive

**Core Features:**
- One-click agent templates (customer service, research, coding assistant)
- Visual workflow builder for agent orchestration
- Built-in testing sandbox with mock data
- Cost tracking per agent and per conversation
- One-click deployment to production

**Unique Value:** Get from idea to working agent prototype in under 30 minutes without touching infrastructure code

**MVP Scope:** Build template system with 3 pre-configured agents, basic visual editor, and local testing. No deployment features in MVP. 8-10 weeks to ship.

**Monetization:** Free tier (local testing only), Pro $29/month (cloud hosting, 10k messages), Team $99/month (unlimited)
```

Content ideas output:
```bash
$ trendsleuth ideas --input analysis.json --type content --count 1
```

```markdown
## Idea 1

**I spent $12,000 on AI agents so you don't have to: The brutal truth about costs**

**Format:** Long-form Twitter/X thread (15-20 tweets) with cost breakdown screenshots

**Target Audience:** Founders, indie hackers, and developers considering implementing AI agents

**Angle:** Expose the hidden costs everyone ignores: API fees compound fast, memory/context management is expensive, failed requests still cost money, and most agents are over-engineered. Share exact cost breakdowns and lessons learned.

**Why It Works:** Combines fear (cost warnings) + value (concrete data) + authority (real experience). Screenshots of bills make it credible. Helps people avoid expensive mistakes. High save/share potential from people wanting to reference it later.
```

## Development

### Contributing

If you want to contribute to TrendSleuth development, follow these steps:

```bash
# Clone the repository
git clone https://github.com/lukemaxwell/trendsleuth.git
cd trendsleuth

# Install with uv (recommended for development)
uv sync

# Activate the virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# The project is automatically installed in editable mode
```

**Note:** The installation instructions above already install TrendSleuth in development mode (`-e` flag), so you don't need to do anything extra.

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
│   ├── ideas.py        # Idea generation from analysis
│   ├── formatter.py    # Output formatting
│   ├── brave.py        # Brave Search API client
│   ├── web_scraper.py  # Web page text extraction
│   └── web_evidence.py # Web evidence gathering
├── tests/
│   ├── test_reddit.py
│   ├── test_analyzer.py
│   ├── test_ideas.py
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
