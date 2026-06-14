from __future__ import annotations

import click

from sage.cli.util import run_async
from sage.memory.store import get_memory_store


@click.command()
@click.option("--repo", required=True, help="GitHub repo in owner/name form.")
def validate(repo: str) -> None:
    """Run lightweight memory integrity checks."""
    result = run_async(_validate(repo))
    if result["errors"]:
        for error in result["errors"]:
            click.echo(f"ERROR: {error}")
        raise click.ClickException("Validation failed")
    click.echo("SAGE validation passed")


async def _validate(repo: str) -> dict:
    store = get_memory_store()
    seen = set()
    errors = []
    for memory in store.memories[repo]:
        if memory.memory_ref in seen:
            errors.append(f"duplicate memory ref {memory.memory_ref}")
        seen.add(memory.memory_ref)
        if not memory.title:
            errors.append(f"{memory.memory_ref} has no title")
    return {"errors": errors}

