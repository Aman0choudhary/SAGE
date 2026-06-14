from sage.github.fetcher import GitHubFetcher, linked_issue_from_text, truncate_diff


def test_linked_issue_from_text_extracts_closing_ref():
    assert linked_issue_from_text("This fixes #42 and adds auth caching.") == 42


def test_truncate_diff_caps_large_diff():
    result = truncate_diff("a" * 20, max_chars=5)
    assert result.startswith("aaaaa")
    assert "truncated" in result


async def test_fetcher_without_token_returns_empty_results(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    fetcher = GitHubFetcher(token=None)

    assert await fetcher.fetch_pull_diff("octo/repo", 1) == ""
    assert await fetcher.list_closed_pulls("octo/repo", 1) == []
