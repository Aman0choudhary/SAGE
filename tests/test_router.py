from sage.router import route


def test_routes_issue_opened_to_premortem():
    payload = {"action": "opened"}
    assert route("issues", payload) == "premortem"


def test_routes_pr_opened_to_review():
    payload = {"action": "opened", "pull_request": {"number": 7}}
    assert route("pull_request", payload) == "pr_review"


def test_routes_merged_pr_to_decision_extractor():
    payload = {"action": "closed", "pull_request": {"merged": True}}
    assert route("pull_request", payload) == "decision_extractor"


def test_routes_sage_ask_before_followup():
    payload = {
        "comment": {"body": '@sage ask "What governs auth?"'},
        "issue": {"number": 1},
    }
    assert route("issue_comment", payload) == "sage_ask"


def test_ignores_bot_issue_comments_to_prevent_self_reply_loop():
    payload = {
        "comment": {
            "body": "SAGE generated pre-mortem",
            "user": {"login": "s-age0[bot]", "type": "Bot"},
        },
        "issue": {"number": 1},
    }
    assert route("issue_comment", payload) == "ignore"


def test_unknown_event_is_ignored():
    assert route("watch", {"action": "started"}) == "ignore"
