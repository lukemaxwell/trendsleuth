"""CLI entry point for TrendSleuth."""

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

from trendsleuth.analyzer import Analyzer, TrendAnalysis
from trendsleuth.config import (
    OpenAIConfig,
    RedditConfig,
    get_config,
    validate_env_vars,
    validate_brave_env,
)
from trendsleuth.formatter import format_json, format_markdown
from trendsleuth.reddit import RedditClient
from trendsleuth.ideas import (
    load_analysis_file,
    generate_ideas,
    format_ideas_as_markdown,
)

logger = logging.getLogger(__name__)

app = typer.Typer(
    name="trendsleuth",
    help="Reddit trend analysis for content creators",
    no_args_is_help=True,
)

console = Console()


@dataclass
class AnalysisContext:
    """Context for a single analysis run."""

    niche: str
    subreddit_list: list[str]
    all_posts: list
    all_comments: list
    analyzed_subreddits: list[str]
    analysis: Optional[TrendAnalysis] = None


class CLIError(Exception):
    """Base exception for CLI errors."""

    pass


def validate_configuration() -> bool:
    """Validate required configuration.
    
    Returns:
        True if configuration is valid, False otherwise.
    """
    missing = validate_env_vars()
    if missing:
        console.print(
            Panel(
                f"[bold red]Missing required environment variables:[/bold red]\n"
                f"  {', '.join(missing)}\n\n"
                "[bold]Please set these in your environment or .env file.",
                title="Configuration Error",
                style="red",
            )
        )
        return False
    return True


def discover_subreddits(
    reddit_client: RedditClient,
    niche: str,
    subreddits: Optional[str],
) -> list[str]:
    """Discover or validate subreddits for the given niche.
    
    Args:
        reddit_client: Reddit API client
        niche: Topic to analyze
        subreddits: Optional comma-separated list of subreddits
        
    Returns:
        List of subreddit names
        
    Raises:
        CLIError: If no subreddits found
    """
    if subreddits:
        return [s.strip() for s in subreddits.split(",")]

    console.print(
        Panel(
            f"[bold cyan]Searching for subreddits related to:[/bold cyan] {niche}",
            title="Discovery",
            style="cyan",
        )
    )
    
    subreddit_list = reddit_client.search_subreddits(niche, limit=5)
    if not subreddit_list:
        raise CLIError(
            "No subreddits found for this niche. "
            "Please try a different topic or specify subreddits manually."
        )

    return subreddit_list


def fetch_subreddit_data(
    reddit_client: RedditClient,
    subreddit_list: list[str],
    post_limit: int,
    comment_limit: int,
) -> tuple[list, list, list[str]]:
    """Fetch posts and comments from all subreddits.
    
    Args:
        reddit_client: Reddit API client
        subreddit_list: List of subreddit names
        post_limit: Maximum posts per subreddit
        comment_limit: Maximum comments per post
        
    Returns:
        Tuple of (all_posts, all_comments, analyzed_subreddits)
        
    Raises:
        CLIError: If no data could be fetched
    """
    all_posts = []
    all_comments = []
    analyzed_subreddits = []

    for subreddit_name in subreddit_list:
        logger.debug(f"Fetching {subreddit_name}...")

        data = reddit_client.get_subreddit_data(
            subreddit_name,
            post_limit=post_limit,
            comment_limit=comment_limit,
        )

        if data["posts"] or data["comments"]:
            all_posts.extend(data["posts"])
            all_comments.extend(data["comments"])
            analyzed_subreddits.append(subreddit_name)
            logger.debug(
                f"Found {len(data['posts'])} posts, {len(data['comments'])} comments"
            )

    if not analyzed_subreddits:
        raise CLIError(
            "No data could be fetched. "
            "Check your Reddit API credentials and internet connection."
        )

    return all_posts, all_comments, analyzed_subreddits


def analyze_content(
    analyzer: Analyzer,
    niche: str,
    posts: list,
    comments: list,
    include_evidence: bool = False,
) -> TrendAnalysis:
    """Analyze the collected content with the LLM.
    
    Args:
        analyzer: Analysis client
        niche: Topic being analyzed
        posts: List of Reddit posts
        comments: List of Reddit comments
        include_evidence: If True, include evidence with quotes and URLs
        
    Returns:
        Analysis results
        
    Raises:
        CLIError: If analysis fails
    """
    console.print(
        Panel(
            "[bold cyan]Analyzing content with AI...",
            title="Analysis",
            style="cyan",
        )
    )

    # Limit input to avoid token issues
    analysis = analyzer.analyze_subreddit_data(
        subreddit_name=f"r/{niche.replace(' ', '-')}",
        posts=posts[:20],
        comments=comments[:200],
        include_evidence=include_evidence,
    )

    if not analysis:
        raise CLIError(
            "Failed to analyze the data. "
            "Please try again with more data or a different model."
        )

    return analysis


def format_output(analysis: TrendAnalysis, output_format: str) -> str:
    """Format the analysis results.
    
    Args:
        analysis: Analysis results
        output_format: Output format ('markdown' or 'json')
        
    Returns:
        Formatted output string
    """
    formatters = {
        "markdown": format_markdown,
        "json": format_json,
    }
    
    formatter = formatters.get(output_format)
    if not formatter:
        raise ValueError(f"Unsupported output format: {output_format}")
    
    return formatter(
        subreddit=analysis.subreddit,
        analysis=analysis,
        token_usage=None,
        cost=None,
    )


def write_output(content: str, output_file: Optional[str]) -> None:
    """Write output to file or stdout.
    
    Args:
        content: Content to write
        output_file: Optional output file path
    """
    if output_file:
        Path(output_file).write_text(content)
        console.print(
            Panel(
                f"[bold green]✓ Results saved to:[/bold green] {output_file}",
                title="Success",
                style="green",
            )
        )
    else:
        console.print("\n")
        console.print(content)


def print_summary(ctx: AnalysisContext, verbose: bool = False) -> None:
    """Print analysis summary.
    
    Args:
        ctx: Analysis context with results
        verbose: If True, print detailed table with metrics
    """
    if not ctx.analysis:
        return
    
    if verbose:
        table = Table(title="Analysis Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_row("Subreddits analyzed", str(len(ctx.analyzed_subreddits)))
        table.add_row("Posts processed", str(len(ctx.all_posts)))
        table.add_row("Comments processed", str(len(ctx.all_comments)))
        table.add_row("Sentiment", ctx.analysis.sentiment)
        
        console.print("\n")
        console.print(table)

    console.print(
        Panel(
            f"[bold green]✓ Analysis complete![/bold green]\n"
            f"  Found {len(ctx.analysis.topics)} topics, "
            f"{len(ctx.analysis.pain_points)} pain points, "
            f"{len(ctx.analysis.questions)} questions",
            title="Done",
            style="green",
        )
    )


def run_analysis_pipeline(
    reddit_config: RedditConfig,
    openai_config: OpenAIConfig,
    niche: str,
    subreddits: Optional[str],
    post_limit: int,
    comment_limit: int,
    include_evidence: bool = False,
    include_web: bool = False,
    web_evidence_limit: int = 15,
    web_results_per_query: int = 5,
    web_rate_limit_rps: float = 1.0,
) -> AnalysisContext:
    """Run the complete analysis pipeline.
    
    Args:
        reddit_config: Reddit API configuration
        openai_config: OpenAI API configuration
        niche: Topic to analyze
        subreddits: Optional comma-separated subreddit list
        post_limit: Maximum posts per subreddit
        comment_limit: Maximum comments per post
        include_evidence: If True, include evidence with quotes and URLs
        include_web: If True, gather web evidence using Brave Search
        web_evidence_limit: Maximum web evidence items to collect
        web_results_per_query: Brave results per query
        web_rate_limit_rps: Brave API rate limit (requests per second)
        
    Returns:
        Analysis context with results
        
    Raises:
        CLIError: If any step fails
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        transient=True,
    ) as progress:
        # Step 1: Discover subreddits
        progress.add_task("[cyan]Discovering relevant subreddits...", total=None)
        reddit_client = RedditClient(reddit_config)
        subreddit_list = discover_subreddits(reddit_client, niche, subreddits)
        logger.info(f"Discovered subreddits: {', '.join(subreddit_list)}")

        # Step 2: Fetch data
        progress.add_task(
            f"[cyan]Fetching data from {len(subreddit_list)} subreddit(s)...",
            total=len(subreddit_list),
        )
        all_posts, all_comments, analyzed_subreddits = fetch_subreddit_data(
            reddit_client, subreddit_list, post_limit, comment_limit
        )

        # Step 3: Analyze with LLM
        progress.add_task("[cyan]Analyzing with AI...", total=None)
        analyzer = Analyzer(openai_config)
        analysis = analyze_content(analyzer, niche, all_posts, all_comments, include_evidence)
        
        # Step 4: Gather web evidence if requested
        if include_web:
            from trendsleuth.config import BraveConfig
            from trendsleuth.web_evidence import gather_web_evidence, WebEvidenceConfig
            
            progress.add_task("[cyan]Gathering web evidence...", total=None)
            
            # Extract Reddit URLs from posts for deduplication
            reddit_urls = set()
            for post in all_posts:
                if hasattr(post, 'permalink'):
                    reddit_urls.add(f"https://reddit.com{post.permalink}")
            
            brave_config = BraveConfig(
                api_key=os.environ.get("BRAVE_API_KEY", ""),
                rate_limit_rps=web_rate_limit_rps,
            )
            
            web_config = WebEvidenceConfig(
                evidence_limit=web_evidence_limit,
                results_per_query=web_results_per_query,
            )
            
            web_evidence = gather_web_evidence(
                niche=niche,
                pain_points=analysis.pain_points,
                questions=analysis.questions,
                topics=analysis.topics,
                brave_config=brave_config,
                web_config=web_config,
                analyzer=analyzer,
                reddit_urls=reddit_urls,
            )
            
            # Merge web evidence with existing evidence
            if analysis.evidence:
                analysis.evidence.extend(web_evidence)
            else:
                analysis.evidence = web_evidence

    return AnalysisContext(
        niche=niche,
        subreddit_list=subreddit_list,
        all_posts=all_posts,
        all_comments=all_comments,
        analyzed_subreddits=analyzed_subreddits,
        analysis=analysis,
    )


@app.command()
def analyze(
    niche: str = typer.Argument(..., help="The niche or topic to analyze"),
    subreddits: Optional[str] = typer.Option(
        None,
        "--subreddits",
        "-s",
        help="Comma-separated list of subreddits (e.g., r/ai,r/machinelearning)",
    ),
    output_file: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: stdout)",
    ),
    limit: int = typer.Option(
        50,
        "--limit",
        "-l",
        help="Maximum number of posts per subreddit",
    ),
    output_format: str = typer.Option(
        "markdown",
        "--format",
        "-f",
        help="Output format (markdown or json)",
    ),
    model: str = typer.Option(
        "gpt-4o-mini",
        "--model",
        help="OpenAI model to use",
    ),
    include_evidence: bool = typer.Option(
        False,
        "--include-evidence",
        help="Include evidence section with verbatim quotes and URLs",
    ),
    include_web: bool = typer.Option(
        False,
        "--include-web",
        help="Gather web evidence using Brave Search (requires BRAVE_API_KEY)",
    ),
    web_evidence_limit: int = typer.Option(
        15,
        "--web-evidence-limit",
        help="Maximum number of web evidence items to collect",
    ),
    web_results_per_query: int = typer.Option(
        5,
        "--web-results-per-query",
        help="Number of Brave search results per query",
    ),
    web_rate_limit_rps: float = typer.Option(
        1.0,
        "--web-rate-limit-rps",
        help="Brave API rate limit (requests per second)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
):
    """Analyze Reddit trends for a given niche."""
    # Configure logging
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
    
    # Validate configuration
    if not validate_configuration():
        raise typer.Exit(code=1)
    
    # Check Brave API key if web evidence requested
    if include_web and not validate_brave_env():
        console.print(
            Panel(
                "[bold red]Missing BRAVE_API_KEY environment variable[/bold red]\n\n"
                "The --include-web flag requires a Brave Search API key.\n"
                "Please set BRAVE_API_KEY in your environment or .env file.",
                title="Configuration Error",
                style="red",
            )
        )
        raise typer.Exit(code=1)

    # Validate format
    if output_format not in ("markdown", "json"):
        console.print(
            Panel(
                f"[bold red]Invalid format: {output_format}. Must be 'markdown' or 'json'",
                title="Error",
                style="red",
            )
        )
        raise typer.Exit(code=1)

    # Load configuration
    reddit_config, openai_config, _, _ = get_config()
    openai_config.model = model

    # Display start message
    console.print(
        Panel(
            f"[bold cyan]TrendSleuth[/bold cyan] - Analyzing niche: [bold]{niche}[/bold]",
            title="Starting Analysis",
            style="cyan",
        )
    )

    try:
        # Run analysis pipeline
        ctx = run_analysis_pipeline(
            reddit_config=reddit_config,
            openai_config=openai_config,
            niche=niche,
            subreddits=subreddits,
            post_limit=limit,
            comment_limit=limit * 2,
            include_evidence=include_evidence,
            include_web=include_web,
            web_evidence_limit=web_evidence_limit,
            web_results_per_query=web_results_per_query,
            web_rate_limit_rps=web_rate_limit_rps,
        )

        # Format and write output
        output_content = format_output(ctx.analysis, output_format)
        write_output(output_content, output_file)

        # Print summary
        print_summary(ctx, verbose=verbose)

    except CLIError as e:
        console.print(
            Panel(
                f"[bold red]{e}[/bold red]",
                title="Error",
                style="red",
            )
        )
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception("Unexpected error during analysis")
        console.print(
            Panel(
                f"[bold red]Unexpected error: {e}[/bold red]",
                title="Error",
                style="red",
            )
        )
        raise typer.Exit(code=1)


@app.command()
def niches(
    theme: str = typer.Option(
        ...,
        "--theme",
        help="Topic or domain to generate niches within (required)",
    ),
    count: int = typer.Option(
        15,
        "--count",
        help="Number of niches to generate",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON array",
    ),
    model: str = typer.Option(
        "gpt-4o-mini",
        "--model",
        help="OpenAI model to use",
    ),
):
    """Generate niche ideas for a given theme."""
    # Validate configuration (only need OpenAI)
    missing = validate_env_vars()
    openai_missing = [var for var in missing if var.startswith("OPENAI_")]
    if openai_missing:
        console.print(
            Panel(
                f"[bold red]Missing required environment variables:[/bold red]\n"
                f"  {', '.join(openai_missing)}\n\n"
                "[bold]Please set these in your environment or .env file.",
                title="Configuration Error",
                style="red",
            )
        )
        raise typer.Exit(code=1)
    
    # Load configuration
    _, openai_config, _, _ = get_config()
    openai_config.model = model
    
    try:
        # Generate niches
        analyzer = Analyzer(openai_config)
        niche_list = analyzer.generate_niches(theme=theme, count=count)
        
        if not niche_list:
            console.print(
                Panel(
                    "[bold red]Failed to generate niches.[/bold red]\n"
                    "Please try again or check your API credentials.",
                    title="Error",
                    style="red",
                )
            )
            raise typer.Exit(code=1)
        
        # Output results
        if output_json:
            print(json.dumps(niche_list, indent=2))
        else:
            for niche in niche_list:
                print(niche)
    
    except Exception as e:
        logger.exception("Unexpected error generating niches")
        console.print(
            Panel(
                f"[bold red]Unexpected error: {e}[/bold red]",
                title="Error",
                style="red",
            )
        )
        raise typer.Exit(code=1)


@app.command()
def ideas(
    input_file: str = typer.Option(
        ...,
        "--input",
        help="Path to TrendSleuth analysis file (JSON or Markdown)",
    ),
    idea_type: str = typer.Option(
        "business",
        "--type",
        help="Type of ideas to generate (business, app, or content)",
    ),
    count: int = typer.Option(
        1,
        "--count",
        help="Number of ideas to generate",
    ),
    output_format: str = typer.Option(
        "md",
        "--format",
        help="Output format (md or json)",
    ),
    model: str = typer.Option(
        "gpt-4o-mini",
        "--model",
        help="OpenAI model to use",
    ),
):
    """Generate ideas from TrendSleuth analysis."""
    # Validate configuration (only need OpenAI)
    missing = validate_env_vars()
    openai_missing = [var for var in missing if var.startswith("OPENAI_")]
    if openai_missing:
        console.print(
            Panel(
                f"[bold red]Missing required environment variables:[/bold red]\n"
                f"  {', '.join(openai_missing)}\n\n"
                "[bold]Please set these in your environment or .env file.",
                title="Configuration Error",
                style="red",
            )
        )
        raise typer.Exit(code=1)
    
    # Validate idea type
    if idea_type not in ('business', 'app', 'content'):
        console.print(
            Panel(
                f"[bold red]Invalid idea type: {idea_type}[/bold red]\n\n"
                "Must be one of: business, app, content",
                title="Error",
                style="red",
            )
        )
        raise typer.Exit(code=1)
    
    # Validate format
    if output_format not in ('md', 'json'):
        console.print(
            Panel(
                f"[bold red]Invalid format: {output_format}[/bold red]\n\n"
                "Must be one of: md, json",
                title="Error",
                style="red",
            )
        )
        raise typer.Exit(code=1)
    
    # Load configuration
    _, openai_config, _, _ = get_config()
    openai_config.model = model
    
    try:
        # Load analysis file
        console.print(
            Panel(
                f"[bold cyan]Loading analysis from:[/bold cyan] {input_file}",
                title="Input",
                style="cyan",
            )
        )
        
        signals = load_analysis_file(input_file)
        
        # Generate ideas
        console.print(
            Panel(
                f"[bold cyan]Generating {count} {idea_type} idea(s)...",
                title="Generation",
                style="cyan",
            )
        )
        
        ideas_data = generate_ideas(
            config=openai_config,
            signals=signals,
            idea_type=idea_type,
            count=count,
        )
        
        # Format output
        if output_format == 'json':
            output = json.dumps(ideas_data, indent=2)
        else:
            output = format_ideas_as_markdown(ideas_data)
        
        # Print to stdout
        console.print("\n")
        console.print(output)
        
    except ValueError as e:
        console.print(
            Panel(
                f"[bold red]{e}[/bold red]",
                title="Error",
                style="red",
            )
        )
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception("Unexpected error generating ideas")
        console.print(
            Panel(
                f"[bold red]Unexpected error: {e}[/bold red]",
                title="Error",
                style="red",
            )
        )
        raise typer.Exit(code=1)


@app.command()
def config(
    show: bool = typer.Option(
        False,
        "--show",
        help="Show current configuration",
    ),
):
    """Manage configuration."""
    if show:
        reddit_config, openai_config, _, brave_config = get_config()

        table = Table(title="Current Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row(
            "Reddit Client ID",
            reddit_config.client_id[:8] + "..." if reddit_config.client_id else "Not set",
        )
        table.add_row("Reddit User Agent", reddit_config.user_agent)
        table.add_row("OpenAI Model", openai_config.model)
        table.add_row(
            "OpenAI API Key",
            "✓ Set" if openai_config.api_key else "Not set",
        )

        console.print("\n")
        console.print(table)
        console.print("\n")


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
):
    """TrendSleuth - Reddit trend analysis for content creators."""
    pass


if __name__ == "__main__":
    app()
