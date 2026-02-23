"""CLI entry point for TrendSleuth."""

import os
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.table import Table

from trendsleuth import __version__
from trendsleuth.config import (
    get_config,
    validate_env_vars,
    AppConfig,
    RedditConfig,
    OpenAIConfig,
)
from trendsleuth.reddit import RedditClient
from trendsleuth.analyzer import Analyzer
from trendsleuth.formatter import format_markdown, format_json


app = typer.Typer(
    name="trendsleuth",
    help="Reddit trend analysis for content creators",
    no_args_is_help=True,
)

console = Console()


def validate_configuration(
    app_config: AppConfig,
    openai_config: OpenAIConfig,
) -> bool:
    """Validate required configuration."""
    missing = validate_env_vars()
    if missing:
        console.print(
            Panel(
                f"[bold red]Missing required environment variables:[/bold red]\n"
                f"  {', '.join(missing)}\n\n"
                f"[bold]Please set these in your environment or .env file.",
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
    verbose: bool,
) -> list[str]:
    """Discover subreddits for the given niche."""
    if subreddits:
        subreddit_list = [s.strip() for s in subreddits.split(",")]
        if verbose:
            console.print(f"[dim]Using specified subreddits: {', '.join(subreddit_list)}[/dim]")
        return subreddit_list

    console.print(
        Panel(
            f"[bold cyan]Searching for subreddits related to:[/bold cyan] {niche}",
            title="Discovery",
            style="cyan",
        )
    )
    subreddit_list = reddit_client.search_subreddits(niche, limit=5)
    if not subreddit_list:
        console.print(
            Panel(
                "[bold yellow]No subreddits found for this niche. "
                "Please try a different topic or specify subreddits manually.",
                title="No Results",
                style="yellow",
            )
        )
        raise typer.Exit(code=1)

    if verbose:
        console.print(f"[dim]Discovered subreddits: {', '.join(subreddit_list)}[/dim]")
    return subreddit_list


def fetch_subreddit_data(
    reddit_client: RedditClient,
    subreddit_list: list[str],
    post_limit: int,
    comment_limit: int,
    verbose: bool,
) -> tuple[list, list, list[str]]:
    """Fetch posts and comments from all subreddits."""
    all_posts = []
    all_comments = []
    analyzed_subreddits = []

    for i, subreddit_name in enumerate(subreddit_list, 1):
        if verbose:
            console.print(f"[dim]Fetching {subreddit_name} ({i}/{len(subreddit_list)})...[/dim]")

        try:
            data = reddit_client.get_subreddit_data(
                subreddit_name,
                post_limit=post_limit,
                comment_limit=comment_limit,
            )

            if data["posts"] or data["comments"]:
                all_posts.extend(data["posts"])
                all_comments.extend(data["comments"])
                analyzed_subreddits.append(subreddit_name)

                if verbose:
                    console.print(
                        f"  ✓ Found {len(data['posts'])} posts, "
                        f"{len(data['comments'])} comments"
                    )
            else:
                if verbose:
                    console.print(f"  ⚠ No data retrieved from {subreddit_name}")

        except Exception as e:
            if verbose:
                console.print(f"  ✗ Error fetching {subreddit_name}: {e}")
            continue

    return all_posts, all_comments, analyzed_subreddits


def analyze_content(
    analyzer: Analyzer,
    niche: str,
    all_posts: list,
    all_comments: list,
    verbose: bool,
) -> Optional:
    """Analyze the collected content with the LLM."""
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
        posts=all_posts[:20],
        comments=all_comments[:200],
    )

    return analysis


def output_results(
    niche: str,
    analysis,
    output: Optional[str],
    format: str,
    analyzed_subreddits: list[str],
    all_posts: list,
    all_comments: list,
    verbose: bool,
) -> None:
    """Format and output results."""
    if verbose:
        console.print("\n[bold]Generating output...[/bold]")

    output_content = format_markdown(
        subreddit=niche,
        analysis=analysis,
        token_usage=None,
        cost=None,
    ) if format == "markdown" else format_json(
        subreddit=niche,
        analysis=analysis,
        token_usage=None,
        cost=None,
    )

    if output:
        with open(output, "w") as f:
            f.write(output_content)
        console.print(
            Panel(
                f"[bold green]✓ Results saved to:[/bold green] {output}",
                title="Success",
                style="green",
            )
        )
    else:
        console.print("\n")
        console.print(output_content)

    # Final summary
    if verbose:
        console.print("\n")
        table = Table(title="Analysis Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_row("Subreddits analyzed", str(len(analyzed_subreddits)))
        table.add_row("Posts processed", str(len(all_posts)))
        table.add_row("Comments processed", str(len(all_comments)))
        table.add_row("Sentiment", analysis.sentiment)
        console.print(table)

    console.print(
        Panel(
            f"[bold green]✓ Analysis complete![/bold green]\n"
            f"  Found {len(analysis.topics)} topics, "
            f"{len(analysis.pain_points)} pain points, "
            f"{len(analysis.questions)} questions",
            title="Done",
            style="green",
        )
    )


@app.command()
def analyze(
    niche: str = typer.Argument(
        ...,
        help="The niche or topic to analyze",
    ),
    subreddits: Optional[str] = typer.Option(
        None,
        "--subreddits",
        "-s",
        help="Comma-separated list of subreddits to analyze (e.g., r/ai,r/machinelearning)",
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
        help="Maximum number of posts to analyze per subreddit",
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
        help="OpenAI model to use for analysis",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose/debug output",
    ),
):
    """Analyze Reddit trends for a given niche."""
    # Get configuration
    reddit_config, openai_config, app_config = get_config()
    openai_config.model = model

    # Validate configuration
    if not validate_configuration(app_config, openai_config):
        raise typer.Exit(code=1)

    # Validate output format
    if format not in ("markdown", "json"):
        console.print(
            Panel(
                f"[bold red]Invalid format: {format}. Must be 'markdown' or 'json'",
                title="Error",
                style="red",
            )
        )
        raise typer.Exit(code=1)

    # Initialize clients
    console.print(
        Panel(
            f"[bold cyan]TrendSleuth[/bold cyan] - Analyzing niche: [bold]{niche}[/bold]",
            title="Starting Analysis",
            style="cyan",
        )
    )

    # Progress tracking
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        transient=True,
    ) as progress:
        # Step 1: Discover subreddits
        task_id = progress.add_task(
            "[cyan]Discovering relevant subreddits...",
            total=None,
        )

        reddit_client = RedditClient(reddit_config)
        subreddit_list = discover_subreddits(
            reddit_client, niche, subreddits, verbose
        )
        progress.update(task_id, completed=True)

        # Step 2: Fetch data from each subreddit
        progress.add_task(
            f"[cyan]Fetching data from {len(subreddit_list)} subreddit(s)...",
            total=len(subreddit_list),
        )

        all_posts, all_comments, analyzed_subreddits = fetch_subreddit_data(
            reddit_client, subreddit_list, limit, limit * 2, verbose
        )

        if not analyzed_subreddits:
            console.print(
                Panel(
                    "[bold red]No data could be fetched. "
                    "Check your Reddit API credentials and internet connection.",
                    title="Error",
                    style="red",
                )
            )
            raise typer.Exit(code=1)

        progress.update(task_id, completed=True)

        # Step 3: Analyze with LLM
        progress.add_task(
            "[cyan]Analyzing with AI...",
            total=None,
        )

        analyzer = Analyzer(openai_config)
        analysis = analyze_content(analyzer, niche, all_posts, all_comments, verbose)

        if not analysis:
            console.print(
                Panel(
                    "[bold red]Failed to analyze the data. "
                    "Please try again with more data or a different model.",
                    title="Analysis Failed",
                    style="red",
                )
            )
            raise typer.Exit(code=1)

        progress.update(task_id, completed=True)

    # Step 4: Format and output results
    output_results(
        niche,
        analysis,
        output,
        format,
        analyzed_subreddits,
        all_posts,
        all_comments,
        verbose,
    )


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
        reddit_config, openai_config, app_config = get_config()

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
    if ctx.invoked_subcommand is None and verbose:
        console.print("[dim]Running in verbose mode...[/dim]")


if __name__ == "__main__":
    app()
