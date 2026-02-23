"""CLI entry point for TrendSleuth."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

from trendsleuth.analyzer import Analyzer, TrendAnalysis
from trendsleuth.config import OpenAIConfig, RedditConfig, get_config, validate_env_vars
from trendsleuth.formatter import format_json, format_markdown
from trendsleuth.reddit import RedditClient

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
) -> TrendAnalysis:
    """Analyze the collected content with the LLM.
    
    Args:
        analyzer: Analysis client
        niche: Topic being analyzed
        posts: List of Reddit posts
        comments: List of Reddit comments
        
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


def print_summary(ctx: AnalysisContext) -> None:
    """Print analysis summary.
    
    Args:
        ctx: Analysis context with results
    """
    if not ctx.analysis:
        return
        
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
) -> AnalysisContext:
    """Run the complete analysis pipeline.
    
    Args:
        reddit_config: Reddit API configuration
        openai_config: OpenAI API configuration
        niche: Topic to analyze
        subreddits: Optional comma-separated subreddit list
        post_limit: Maximum posts per subreddit
        comment_limit: Maximum comments per post
        
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
        analysis = analyze_content(analyzer, niche, all_posts, all_comments)

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
    output: Optional[str] = typer.Option(
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
    format: str = typer.Option(
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

    # Validate format
    if format not in ("markdown", "json"):
        console.print(
            Panel(
                f"[bold red]Invalid format: {format}. Must be 'markdown' or 'json'",
                title="Error",
                style="red",
            )
        )
        raise typer.Exit(code=1)

    # Load configuration
    reddit_config, openai_config, _ = get_config()
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
        )

        # Format and write output
        output_content = format_output(ctx.analysis, format)
        write_output(output_content, output)

        # Print summary
        if verbose:
            print_summary(ctx)
        else:
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
def config(
    show: bool = typer.Option(
        False,
        "--show",
        help="Show current configuration",
    ),
):
    """Manage configuration."""
    if show:
        reddit_config, openai_config, _ = get_config()

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
