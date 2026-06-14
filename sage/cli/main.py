from __future__ import annotations

import click

from sage.cli.dashboard import generate_dashboard_file
from sage.cli.migrate import migrate
from sage.cli.stats import stats
from sage.cli.util import run_async
from sage.cli.validate import validate


@click.group()
def cli() -> None:
    """SAGE command line tools."""


@click.command()
@click.option("--repo", required=True, help="GitHub repo in owner/name form.")
@click.option("--output", default="sage-dashboard.html", show_default=True)
def dashboard(repo: str, output: str) -> None:
    """Generate a self-contained HTML dashboard."""
    path = run_async(generate_dashboard_file(repo, output))
    click.echo(f"Dashboard written to {path}")


cli.add_command(migrate)
cli.add_command(validate)
cli.add_command(stats)
cli.add_command(dashboard)


if __name__ == "__main__":
    cli()

