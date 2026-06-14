from __future__ import annotations

import json

import click

from sage.cli.util import run_async
from sage.memory.store import get_memory_store


@click.command()
@click.option("--repo", required=True, help="GitHub repo in owner/name form.")
def stats(repo: str) -> None:
    """Print SAGE memory stats as JSON."""
    result = run_async(get_memory_store().stats(repo))
    click.echo(json.dumps(result, indent=2))

