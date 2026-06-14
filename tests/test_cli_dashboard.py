from sage.cli.dashboard import generate_dashboard_file


async def test_dashboard_generation_creates_parent_directory(tmp_path):
    output = tmp_path / "nested" / "sage-dashboard.html"

    path = await generate_dashboard_file("octo/repo", output)

    assert path.exists()
    assert "SAGE Dashboard" in path.read_text(encoding="utf-8")
