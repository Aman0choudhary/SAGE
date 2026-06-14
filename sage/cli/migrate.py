from __future__ import annotations

import click

from sage.agents.decision_extractor import run_decision_extractor
from sage.cli.util import run_async
from sage.config import get_settings
from sage.dispatcher import resolve_vector_store_id
from sage.github.fetcher import GitHubFetcher


@click.command()
@click.option("--repo", required=True, help="GitHub repo in owner/name form.")
@click.option("--limit", default=200, show_default=True)
def migrate(repo: str, limit: int) -> None:
    """Import past PRs retroactively into SAGE memory."""
    result = run_async(_migrate(repo, limit))
    click.echo(
        f"Migration complete for {repo}: scanned {result['scanned']} closed PRs, "
        f"processed {result['processed']} merged PRs."
    )


async def _migrate(repo: str, limit: int) -> dict[str, int]:
    settings = get_settings()
    if not settings.github_token:
        raise click.ClickException("Set GITHUB_TOKEN before running sage migrate.")

    fetcher = GitHubFetcher(token=settings.github_token)
    vector_store_id = await resolve_vector_store_id(repo)
    pulls = await fetcher.list_closed_pulls(repo, limit=limit)
    processed = 0

    with click.progressbar(pulls, label="Importing merged PRs") as bar:
        for pr in bar:
            if not pr.get("merged_at"):
                continue
            number = int(pr["number"])
            diff = await fetcher.fetch_pull_diff(repo, number)
            comments = await fetcher.fetch_pr_conversation(repo, number)
            await run_decision_extractor(
                repo=repo,
                pr_number=number,
                comments=comments,
                diff=diff,
                vector_store_id=vector_store_id,
                github_token=settings.github_token,
            )
            processed += 1

    return {"scanned": len(pulls), "processed": processed}
