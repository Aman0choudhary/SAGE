# SAGE — Semantic Agentic Git Engine
## Complete Project Plan (OpenAI Codex Hackathon Edition)

> **Stack: GPT-5.5 · OpenAI Responses API · Vector Stores · $50 API Credits**

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Why GPT-5.5 + Responses API (Not Chat Completions)](#2-why-gpt-55--responses-api)
3. [Architecture Overview](#3-architecture-overview)
4. [Tech Stack](#4-tech-stack)
5. [Folder Structure](#5-folder-structure)
6. [Database Schema](#6-database-schema)
7. [OpenAI Setup (Vector Store + API)](#7-openai-setup)
8. [GitHub App Setup](#8-github-app-setup)
9. [Agent Breakdown](#9-agent-breakdown)
10. [Custom Function Tools](#10-custom-function-tools)
11. [API Endpoints](#11-api-endpoints)
12. [Memory System](#12-memory-system)
13. [CLI Tool](#13-cli-tool)
14. [Dashboard](#14-dashboard)
15. [Environment Variables](#15-environment-variables)
16. [Build Phases + Day-by-Day Order](#16-build-phases)
17. [Testing Plan](#17-testing-plan)
18. [Deployment](#18-deployment)
19. [Credit Usage Estimate](#19-credit-usage-estimate)
20. [Differentiators Over LORE](#20-differentiators-over-lore)

---

## 1. Project Overview

### Problem
PR decisions die in comment threads. New devs have zero context on *why* the codebase is the way it is. The same bugs get introduced, reviewed, caught, and fixed — over and over.

### Solution
SAGE is a GitHub App powered by **GPT-5.5 via OpenAI Responses API** that:
- Gives your codebase **institutional memory** stored in OpenAI Vector Stores
- **Predicts failures** before code is written (pre-mortem on issues)
- Does a **5-layer AI review** on every PR (including live CVE web search)
- **Extracts and stores decisions** from merged PRs automatically
- **Enforces** past decisions on future PRs semantically
- **Answers questions** about your codebase history with `@sage ask`
- **Onboards** new devs with full historical context

---

## 2. Why GPT-5.5 + Responses API

This is NOT the old Chat Completions API. Key differences:

```
Chat Completions (OLD way):
  You → build prompt → call API → parse text output → do action manually

Responses API (NEW way):
  You → give GPT-5.5 a goal + tools → it calls tools itself → done
```

### GPT-5.5 Built-in Tools Available to SAGE

| Tool | How SAGE Uses It |
|---|---|
| `file_search` | Semantic search across all stored decisions (Vector Store) |
| `web_search` | Live CVE lookup during Security Sentinel layer |
| `code_interpreter` | Actually run analysis on PR diffs |
| `function_calling` | Your custom tools: post GitHub comment, store memory, etc. |
| `computer_use` | Demo bonus: Codex can navigate GitHub UI |

GPT-5.5 supports **1M token context window** — entire PR history in one call.

### The API Call Pattern for Every Agent

```python
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

response = client.responses.create(
    model="gpt-5.5",
    instructions="You are SAGE...",   # system prompt
    input="Issue opened: ...",         # user input
    tools=[
        {"type": "file_search", "vector_store_ids": [VECTOR_STORE_ID]},
        {"type": "web_search"},
        {
            "type": "function",
            "name": "post_github_comment",
            "description": "Post a comment to a GitHub Issue or PR",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string"},
                    "number": {"type": "integer"},
                    "body": {"type": "string"}
                },
                "required": ["repo", "number", "body"]
            }
        }
    ]
)
```

---

## 3. Architecture Overview

```
GitHub Events (Webhooks)
         │
         ▼
┌─────────────────────┐
│   FastAPI Server    │  ← Receives webhooks, validates HMAC signature
│   (app.py)          │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Triage Router     │  ← Classifies event, dispatches to agent
│   (router.py)       │
└────────┬────────────┘
         │
    ┌────┴──────────────────────────────────────────────────┐
    │                                                       │
    ▼                                                       ▼
Event-Triggered Agents                           On-Demand Agents
──────────────────────                           ────────────────
Pre-Mortem Agent     (issue opened)              SAGE Ask
Follow-Up Agent      (issue comment)             Onboarding Agent
PR Review Agent      (PR opened/updated)         Health Auditor
Reply Handler        (sage: commands on PR)
Decision Extractor   (PR merged)
Commit Keeper        (push)

         │
         │  Every agent uses:
         ▼
┌──────────────────────────────────────────────────────┐
│              OpenAI Responses API (GPT-5.5)          │
│                                                      │
│  Tools:                                              │
│  ├── file_search → OpenAI Vector Store (memory)     │
│  ├── web_search  → Live CVE / docs lookup            │
│  ├── code_interpreter → Analyze diffs                │
│  └── function_calling → Your custom tools below     │
└──────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────┐     ┌─────────────────────────┐
│  OpenAI Vector      │     │   Supabase (Postgres)   │
│  Store              │     │   Structured metadata:  │
│  (semantic memory)  │     │   promises, patterns,   │
│                     │     │   ledger, config        │
└─────────────────────┘     └─────────────────────────┘
         │
         ▼
┌─────────────────────┐
│   GitHub API        │  ← Post comments, fetch diffs, tag users
│   (PyGithub)        │
└─────────────────────┘
```

---

## 4. Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Language | Python 3.11+ | Clean async, rich ecosystem |
| Web Server | FastAPI | Async webhooks, fast |
| LLM | **GPT-5.5 via OpenAI Responses API** | Native tools, 1M context, agentic |
| Semantic Memory | **OpenAI Vector Stores + file_search** | No pgvector setup needed, auto embeddings |
| Structured DB | Supabase (Postgres) | Promises, patterns, ledger, config |
| GitHub Integration | PyGithub | Full GitHub API access |
| CLI | Python Click | `sage migrate`, `sage dashboard` |
| Dashboard | Self-contained HTML + Mermaid.js | No frontend framework needed |
| Hosting | Railway or Render | Easy deploy, free tier available |
| Testing | pytest + pytest-asyncio | Unit + integration tests |

### Key Packages

```txt
# requirements.txt
openai>=1.80.0          # Responses API + Vector Stores
fastapi
uvicorn
PyGithub
supabase
python-dotenv
click
pytest
pytest-asyncio
httpx                   # For async HTTP in tests
```

---

## 5. Folder Structure

```
sage/
│
├── app.py                          # FastAPI entrypoint
├── router.py                       # Triage Router
├── requirements.txt
├── .env.example
├── README.md
│
├── agents/
│   ├── __init__.py
│   ├── premortem.py                # Issue opened → pre-mortem
│   ├── followup.py                 # Issue comment → evaluate answers
│   ├── pr_review.py                # PR opened → 5-layer review
│   ├── reply_handler.py            # sage: commands
│   ├── decision_extractor.py       # PR merged → extract + store
│   ├── commit_keeper.py            # Push → ledger entry
│   ├── sage_ask.py                 # @sage ask
│   ├── onboarding.py               # @sage onboard
│   └── health_auditor.py           # @sage health
│
├── memory/
│   ├── __init__.py
│   ├── vector_store.py             # OpenAI Vector Store CRUD
│   ├── store.py                    # Save to Supabase (structured data)
│   └── models.py                   # Pydantic models
│
├── tools/
│   ├── __init__.py
│   ├── definitions.py              # All function tool JSON definitions
│   └── handlers.py                 # Execute tool calls from GPT-5.5
│
├── github/
│   ├── __init__.py
│   ├── webhooks.py                 # Parse + validate webhooks
│   ├── comments.py                 # Post/edit GitHub comments
│   ├── fetcher.py                  # Fetch diffs, issues, commit history
│   └── auth.py                     # GitHub App JWT auth
│
├── prompts/
│   ├── premortem.txt
│   ├── followup.txt
│   ├── pr_review.txt
│   ├── decision_extract.txt
│   ├── sage_ask.txt
│   ├── onboarding.txt
│   └── health_audit.txt
│
├── cli/
│   ├── __init__.py
│   ├── main.py                     # Click entrypoint
│   ├── migrate.py                  # sage migrate
│   ├── validate.py                 # sage validate
│   ├── stats.py                    # sage stats
│   └── dashboard.py                # sage dashboard
│
├── dashboard/
│   └── template.html
│
└── tests/
    ├── test_router.py
    ├── test_premortem.py
    ├── test_pr_review.py
    ├── test_decision_extractor.py
    ├── test_memory_vector_store.py
    ├── test_tools_handlers.py
    ├── test_webhooks.py
    ├── test_sage_ask.py
    ├── test_onboarding.py
    ├── test_commit_keeper.py
    └── test_cli_migrate.py
```

---

## 6. Database Schema

Only structured relational data goes in Supabase. Semantic memory goes in OpenAI Vector Store.

```sql
-- Structured metadata for decisions (semantic content in Vector Store)
CREATE TABLE memories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_full_name TEXT NOT NULL,
  memory_ref TEXT NOT NULL,              -- "SAGE-MEMORY-001"
  memory_type TEXT NOT NULL,             -- 'decision' | 'rule' | 'incident' | 'promise'
  title TEXT NOT NULL,
  vector_store_file_id TEXT,             -- OpenAI file ID in Vector Store
  source_type TEXT NOT NULL,             -- 'pr' | 'issue' | 'commit'
  source_id INTEGER,
  source_url TEXT,
  author_github TEXT,
  files_affected TEXT[],
  domains TEXT[],
  risk_level TEXT,
  is_overridden BOOLEAN DEFAULT FALSE,
  overridden_by UUID REFERENCES memories(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Reviewer-stated rules enforced on every PR
CREATE TABLE patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_full_name TEXT NOT NULL,
  pattern_ref TEXT NOT NULL,             -- "SAGE-PATTERN-001"
  rule TEXT NOT NULL,
  source_pr INTEGER,
  stated_by TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  violation_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Developer promises from issues, verified on PR
CREATE TABLE promises (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_full_name TEXT NOT NULL,
  issue_number INTEGER NOT NULL,
  pr_number INTEGER,
  promise TEXT NOT NULL,
  status TEXT DEFAULT 'pending',         -- 'pending' | 'kept' | 'broken'
  made_by TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Structured push log
CREATE TABLE commit_ledger (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_full_name TEXT NOT NULL,
  commit_sha TEXT NOT NULL,
  author TEXT NOT NULL,
  files_changed TEXT[],
  domains_touched TEXT[],
  breaking_risk TEXT,
  committed_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Per-repo SAGE config + counters
CREATE TABLE repo_config (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_full_name TEXT UNIQUE NOT NULL,
  openai_vector_store_id TEXT,           -- One Vector Store per repo
  memory_counter INTEGER DEFAULT 0,
  pattern_counter INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  installed_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 7. OpenAI Setup

### Vector Store (One Per Repo)

When a new repo installs SAGE, create a vector store:

```python
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

def create_repo_vector_store(repo_full_name: str) -> str:
    vs = client.vector_stores.create(
        name=f"sage-{repo_full_name.replace('/', '-')}",
        expires_after={"anchor": "last_active_at", "days": 365}
    )
    return vs.id  # Store this in repo_config table
```

### Storing a Decision in Vector Store

```python
def store_memory_in_vector_store(
    vector_store_id: str,
    memory_ref: str,
    content: str,        # Full decision text
    metadata: dict
) -> str:
    # Upload as a text file
    file_content = f"""
MEMORY REF: {memory_ref}
TYPE: {metadata['type']}
AUTHOR: {metadata['author']}
DATE: {metadata['date']}
FILES: {', '.join(metadata.get('files', []))}
DOMAINS: {', '.join(metadata.get('domains', []))}

DECISION:
{content}
""".encode()

    file = client.files.create(
        file=("memory.txt", file_content, "text/plain"),
        purpose="assistants"
    )

    client.vector_stores.files.create(
        vector_store_id=vector_store_id,
        file_id=file.id
    )

    return file.id
```

### Searching Memory (Automatic via file_search tool)

No manual search code needed. GPT-5.5 does it automatically when you pass `file_search` as a tool.

---

## 8. GitHub App Setup

### Create the App
1. GitHub → Settings → Developer Settings → GitHub Apps → New
2. Configure:
```
App Name: SAGE
Webhook URL: https://your-sage-url.com/webhook
Webhook Secret: (generate strong random string)

Permissions:
  Issues: Read & Write
  Pull Requests: Read & Write
  Contents: Read
  Metadata: Read

Subscribe to Events:
  ✅ Issues
  ✅ Issue comments
  ✅ Pull requests
  ✅ Pull request review comments
  ✅ Push
```
3. Download Private Key (.pem)
4. Note App ID + Installation ID

### Webhook Validation

```python
import hmac, hashlib

def validate_github_signature(payload: bytes, sig_header: str, secret: str) -> bool:
    expected = "sha256=" + hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, sig_header)
```

---

## 9. Agent Breakdown

### How Every Agent Works (The Pattern)

```python
# 1. Receive GitHub event context
# 2. Build the input string
# 3. Call client.responses.create() with tools
# 4. Process tool_call outputs in a loop
# 5. Let GPT-5.5 call your function tools
# 6. Return results back to GPT-5.5 until done

async def run_agent(instructions: str, input_text: str, tools: list, 
                    vector_store_id: str, repo: str, number: int):
    
    response = client.responses.create(
        model="gpt-5.5",
        instructions=instructions,
        input=input_text,
        tools=tools
    )
    
    # Process any tool calls GPT-5.5 makes
    while response.status == "requires_action":
        tool_outputs = []
        for tool_call in response.required_action.submit_tool_outputs.tool_calls:
            result = await execute_tool(tool_call.function.name, 
                                        tool_call.function.arguments,
                                        repo=repo, number=number)
            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": str(result)
            })
        
        # Continue the response
        response = client.responses.submit_tool_outputs(
            response_id=response.id,
            tool_outputs=tool_outputs
        )
    
    return response
```

---

### Agent 1: Pre-Mortem Agent (`agents/premortem.py`)

**Trigger:** Issue opened

```python
async def run_premortem(repo: str, issue_number: int, title: str, body: str,
                        vector_store_id: str):

    instructions = """
You are SAGE — a senior engineer with perfect memory of this codebase.
A new issue has been opened. Your job:
1. Search past decisions and incidents for related failures
2. Write a brutal pre-mortem: what could go wrong, and WHY based on real past incidents
3. Ask the developer 3-5 hard questions they must answer before coding
4. Set acceptance criteria based on past failures
5. Assign a risk level: LOW / MEDIUM / HIGH / CRITICAL
6. Post the pre-mortem as a GitHub comment using the post_github_comment tool

Format your comment with: Risk Level, What Could Go Wrong, Past Decisions Found,
Hard Questions, and Acceptance Criteria.
Speak as a senior engineer who was there when things broke. Not corporate. Direct.
"""

    input_text = f"New issue #{issue_number}: {title}\n\n{body}"

    tools = [
        {"type": "file_search", "vector_store_ids": [vector_store_id]},
        TOOL_POST_GITHUB_COMMENT,
        TOOL_SET_GITHUB_LABEL,
        TOOL_STORE_PROMISE_PLACEHOLDERS,
    ]

    await run_agent(instructions, input_text, tools, vector_store_id, repo, issue_number)
```

**Output Comment:**
```
## 🔍 SAGE Pre-Mortem — Issue #43

**Risk Level:** 🔴 HIGH

### What Could Go Wrong
Based on SAGE-MEMORY-042 (Sep 2024 incident): This team has already shipped
a cache invalidation bug in auth. In-memory or Redis caching of auth tokens
caused users to authenticate with revoked credentials for 120 minutes.

### Hard Questions
1. How will cache invalidate on password reset?
2. What is your exact TTL and why that number?
3. Have you read SAGE-MEMORY-042?

### Acceptance Criteria
- [ ] No auth responses cached without explicit TTL ≤ 30s
- [ ] Cache invalidation tested on token revocation
- [ ] Load tested under 10k concurrent users

_Reply to this comment. SAGE is watching._
```

---

### Agent 2: Follow-Up Agent (`agents/followup.py`)

**Trigger:** Developer comments on an issue that has a SAGE pre-mortem

```python
instructions = """
You are SAGE. A developer has replied to your pre-mortem.
1. Evaluate whether they answered your questions satisfactorily
2. Extract any promises they made ("I will use bcrypt", "TTL will be 30s")
3. Store each promise using the store_promise tool
4. If answers are good: acknowledge and wish them luck
5. If answers are vague/wrong: push back with specific follow-up questions
6. Post your response using post_github_comment
"""
```

Tools: `file_search`, `post_github_comment`, `store_promise`, `get_premortem_questions`

---

### Agent 3: PR Review Agent (`agents/pr_review.py`) ⭐ Most Important

**Trigger:** PR opened or updated

```python
instructions = """
You are SAGE. Review this PR across exactly 5 layers. For each layer,
search for relevant information and provide specific findings.

LAYER 1 — MEMORY CONFLICTS:
Search the vector store for past decisions that conflict with this PR.
Don't just keyword match — reason about whether the PATTERN is the same.
"In-memory dict caching of auth" IS the same failure as "Redis caching of auth tokens".

LAYER 2 — PROMISE VERIFICATION:
Check each stored promise from the linked issue against the actual code.
Be specific: "You promised 30s TTL. Line 47 sets 1800s. That's 60x your promise."

LAYER 3 — SECURITY SENTINEL:
Search the vector store for past security decisions.
Use web_search to look up any new dependencies for known CVEs.
Flag: SQL injection patterns, weak hashing, eval on untrusted data, hardcoded secrets.

LAYER 4 — CODE INTELLIGENCE:
From the diff: new dependencies introduced? Architecture changing?
Tech drift from established patterns? New failure modes introduced?

LAYER 5 — PATTERN ENFORCEMENT:
Get active patterns from store. Check each one against the diff.
If reviewer once said "never use sync Redis in async context" — check for it.

After all layers: post ONE structured comment with all findings.
End with: sage-memory refs used, overall risk level, and the 3 options:
sage: intentional | sage: accidental | sage: discuss
"""

tools = [
    {"type": "file_search", "vector_store_ids": [vector_store_id]},
    {"type": "web_search"},                    # ← CVE lookup, docs
    TOOL_GET_PROMISES,                          # Fetch stored promises
    TOOL_GET_ACTIVE_PATTERNS,                   # Fetch enforced rules
    TOOL_POST_GITHUB_COMMENT,
    TOOL_SET_GITHUB_LABEL,
]

input_text = f"""
PR #{pr_number}: {pr_title}
Linked Issue: #{linked_issue}
Author: {author}

PR Description:
{pr_body}

Diff:
{diff[:40000]}  # Truncate huge diffs
"""
```

**Output Comment:**
```
## 🧠 SAGE Review — PR #47

### Layer 1: Memory Conflicts 🔴
CONFLICT with SAGE-MEMORY-042:
This implements in-memory caching of auth tokens — the same pattern that
caused the Sep 2024 outage. The failure mode is identical: cache won't
invalidate on password reset.

→ `sage: intentional` (with reasoning) | `sage: accidental` | `sage: discuss`

### Layer 2: Promise Verification 🟡
From Issue #43:
✅ "bcrypt with cost 12" — confirmed line 23
❌ "30 second TTL" — code sets 1800s (line 47). 60x your promise.
⚠️  "invalidation on logout" — not found in diff

### Layer 3: Security Sentinel ✅
web_search: redis 5.0.1 — no critical CVEs found (checked June 2026)
No SQL injection patterns. No weak hashing detected.
Cross-referenced 12 stored security decisions — all clear.

### Layer 4: Code Intelligence ℹ️
New dependency: redis==5.0.1 (not previously used in auth service)
Architecture change: introducing cache layer to stateless auth service
No breaking API changes in public endpoints.

### Layer 5: Pattern Enforcement 🔴
SAGE-PATTERN-007 violated: "No sync Redis calls in async context"
(Stated by @senior-dev, PR #31, Jan 2025)
Violation found: line 89 — `redis_client.get()` in async function

---
Risk: 🔴 HIGH | SAGE-MEMORY-042, SAGE-PATTERN-007
```

---

### Agent 4: Reply Handler (`agents/reply_handler.py`)

**Trigger:** PR comment containing `sage: intentional`, `sage: accidental`, or `sage: discuss`

```python
# sage: intentional [reasoning]
instructions_intentional = """
Developer has overridden a SAGE finding with reasoning.
1. Read their reasoning carefully
2. Evaluate if it's sound
3. Update the memory: mark old decision as overridden, create new one
4. Check if their code actually matches their stated reasoning
5. Post acknowledgment: "Memory updated. Holding you to [new commitment]."
"""
tools: store_memory, update_memory, post_github_comment, file_search

# sage: accidental
instructions_accidental = """
Developer acknowledges the issue was accidental.
1. Post acknowledgment
2. Mark the conflict as "being fixed"
3. Note which memory ref triggered this
"""
tools: post_github_comment, update_promise_status

# sage: discuss
instructions_discuss = """
Developer wants to discuss the original decision.
1. Find the original decision in vector store
2. Find the original author's GitHub handle
3. Tag them and the decision makers in a comment
4. Frame the discussion clearly
"""
tools: file_search, post_github_comment, get_memory_authors
```

---

### Agent 5: Decision Extractor (`agents/decision_extractor.py`)

**Trigger:** PR merged

```python
instructions = """
A PR has been merged. Extract ALL decisions from it.

From the COMMENTS: Extract decisions, rules stated by reviewers, commitments made.
From the DIFF: Extract architectural choices, technology decisions, patterns established.

For each decision:
- Is it a 'decision', 'rule', 'incident_lesson', or 'pattern'?
- What's the reasoning behind it?
- Which files/domains does it apply to?
- Who made it?

Ignore noise: "LGTM", "thanks", style nits.
Focus on: "we decided X because Y", "never do Z", "always use W for this case"

Store each using store_memory tool.
Post a summary comment: "SAGE captured N decisions from this PR"
"""

tools = [
    TOOL_STORE_MEMORY,          # saves to Vector Store + Supabase
    TOOL_STORE_PATTERN,         # saves reviewer rules
    TOOL_POST_GITHUB_COMMENT,
    TOOL_INCREMENT_COUNTER,
]
```

---

### Agent 6: Commit Keeper (`agents/commit_keeper.py`)

**Trigger:** Push event (lightweight)

```python
instructions = """
A push was made. Write a structured ledger entry:
- Classify files into domains (auth, payments, db, api, tests, infra)
- Assess breaking change risk based on what was changed
- Check if any high-risk files were touched (search vector store)
- If high-risk files touched + related memories exist: open a GitHub issue as warning
"""

tools = [
    {"type": "file_search", "vector_store_ids": [vector_store_id]},
    TOOL_STORE_LEDGER_ENTRY,
    TOOL_CREATE_GITHUB_ISSUE,   # Only if high risk
]
```

---

### Agent 7: SAGE Ask (`agents/sage_ask.py`)

**Trigger:** `@sage ask "What decisions govern our auth system?"` anywhere

```python
instructions = """
Answer the developer's question using your memory of this codebase.
Search the vector store for relevant decisions.
Answer like a senior engineer who was there — specific, named, dated.
Format: decision ref, date, who made it, what was decided, why.
If you don't know, say so. Don't hallucinate decisions.
"""

tools = [
    {"type": "file_search", "vector_store_ids": [vector_store_id]},
    {"type": "web_search"},     # For questions needing external context
    TOOL_POST_GITHUB_COMMENT,
]
```

---

### Agent 8: Onboarding Agent (`agents/onboarding.py`)

**Trigger:** `@sage onboard @username`

```python
instructions = """
Generate a complete onboarding briefing for a new team member.
Structure it as:

1. SECURITY FIRST — all security decisions they must know
2. ARCHITECTURE — how the codebase is structured, key decisions per domain
3. PAST INCIDENTS — what broke, when, what was learned
4. KEY PEOPLE — who owns what (from memory authors)
5. FORBIDDEN PATTERNS — things explicitly prohibited and why
6. RECENT CHANGES — last 30 days of significant decisions

Be specific. Use actual memory refs. This person's first week depends on this.
"""

tools = [
    {"type": "file_search", "vector_store_ids": [vector_store_id]},
    TOOL_GET_RECENT_LEDGER,
    TOOL_GET_ACTIVE_PATTERNS,
    TOOL_POST_GITHUB_COMMENT,
]
```

---

### Agent 9: Health Auditor (`agents/health_auditor.py`)

**Trigger:** `@sage health`

```python
instructions = """
Generate a health report for this codebase's decision memory.

Analyse:
- Decision coverage: which domains have strong memory vs gaps
- Stale decisions: >1 year old, might be outdated
- Conflicting decisions: search for semantic contradictions
- Pattern violation rate: which rules get broken most
- Promise tracking: kept vs broken ratio
- Security inventory: all security decisions in one place

Then call generate_dashboard to produce the HTML report.
Post the link using post_github_comment.
"""

tools = [
    {"type": "file_search", "vector_store_ids": [vector_store_id]},
    TOOL_GET_ALL_PATTERNS,
    TOOL_GET_PROMISE_STATS,
    TOOL_GET_LEDGER_SUMMARY,
    TOOL_GENERATE_DASHBOARD,    # Creates HTML file, returns URL
    TOOL_POST_GITHUB_COMMENT,
]
```

---

## 10. Custom Function Tools

All function tools GPT-5.5 can call. Define in `tools/definitions.py`:

```python
TOOL_POST_GITHUB_COMMENT = {
    "type": "function",
    "name": "post_github_comment",
    "description": "Post a comment to a GitHub Issue or PR",
    "parameters": {
        "type": "object",
        "properties": {
            "repo": {"type": "string", "description": "owner/repo"},
            "number": {"type": "integer", "description": "Issue or PR number"},
            "body": {"type": "string", "description": "Markdown comment body"}
        },
        "required": ["repo", "number", "body"]
    }
}

TOOL_STORE_MEMORY = {
    "type": "function",
    "name": "store_memory",
    "description": "Store a decision in SAGE memory (Vector Store + Supabase)",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "content": {"type": "string", "description": "Full decision text"},
            "memory_type": {"type": "string", "enum": ["decision", "rule", "incident", "pattern"]},
            "author": {"type": "string"},
            "files_affected": {"type": "array", "items": {"type": "string"}},
            "domains": {"type": "array", "items": {"type": "string"}},
            "risk_level": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
            "source_pr": {"type": "integer"}
        },
        "required": ["title", "content", "memory_type"]
    }
}

TOOL_GET_ACTIVE_PATTERNS = {
    "type": "function",
    "name": "get_active_patterns",
    "description": "Get all active enforced patterns for this repo",
    "parameters": {
        "type": "object",
        "properties": {
            "repo": {"type": "string"}
        },
        "required": ["repo"]
    }
}

TOOL_STORE_PROMISE = {
    "type": "function",
    "name": "store_promise",
    "description": "Store a developer promise from an issue for later verification",
    "parameters": {
        "type": "object",
        "properties": {
            "repo": {"type": "string"},
            "issue_number": {"type": "integer"},
            "promise": {"type": "string"},
            "made_by": {"type": "string"}
        },
        "required": ["repo", "issue_number", "promise"]
    }
}

TOOL_GET_PROMISES = {
    "type": "function",
    "name": "get_promises",
    "description": "Get all promises made on a specific issue",
    "parameters": {
        "type": "object",
        "properties": {
            "repo": {"type": "string"},
            "issue_number": {"type": "integer"}
        },
        "required": ["repo", "issue_number"]
    }
}

TOOL_SET_GITHUB_LABEL = {
    "type": "function",
    "name": "set_github_label",
    "description": "Apply a label to a GitHub Issue or PR",
    "parameters": {
        "type": "object",
        "properties": {
            "repo": {"type": "string"},
            "number": {"type": "integer"},
            "label": {"type": "string", "description": "e.g. 'sage-risk: high'"}
        },
        "required": ["repo", "number", "label"]
    }
}

TOOL_STORE_PATTERN = {
    "type": "function",
    "name": "store_pattern",
    "description": "Store a reviewer-stated rule as a permanent enforced pattern",
    "parameters": {
        "type": "object",
        "properties": {
            "repo": {"type": "string"},
            "rule": {"type": "string"},
            "source_pr": {"type": "integer"},
            "stated_by": {"type": "string"}
        },
        "required": ["repo", "rule", "source_pr"]
    }
}

TOOL_UPDATE_MEMORY = {
    "type": "function",
    "name": "update_memory",
    "description": "Override an existing memory with new reasoning",
    "parameters": {
        "type": "object",
        "properties": {
            "memory_ref": {"type": "string"},
            "new_content": {"type": "string"},
            "override_reason": {"type": "string"},
            "overridden_by": {"type": "string"}
        },
        "required": ["memory_ref", "new_content", "override_reason"]
    }
}

TOOL_STORE_LEDGER_ENTRY = {
    "type": "function",
    "name": "store_ledger_entry",
    "description": "Write a structured commit log entry",
    "parameters": {
        "type": "object",
        "properties": {
            "repo": {"type": "string"},
            "commit_sha": {"type": "string"},
            "author": {"type": "string"},
            "files_changed": {"type": "array", "items": {"type": "string"}},
            "domains_touched": {"type": "array", "items": {"type": "string"}},
            "breaking_risk": {"type": "string", "enum": ["low", "medium", "high"]}
        },
        "required": ["repo", "commit_sha", "author"]
    }
}
```

Implement all handlers in `tools/handlers.py`:

```python
async def execute_tool(tool_name: str, arguments: dict, repo: str, number: int):
    if tool_name == "post_github_comment":
        return await github_comments.post(arguments["repo"], arguments["number"], arguments["body"])
    elif tool_name == "store_memory":
        return await memory_store.save(repo=repo, **arguments)
    elif tool_name == "get_active_patterns":
        return await supabase.get_patterns(repo)
    elif tool_name == "store_promise":
        return await supabase.insert_promise(**arguments)
    elif tool_name == "get_promises":
        return await supabase.get_promises(arguments["repo"], arguments["issue_number"])
    # ... etc
```

---

## 11. API Endpoints

```python
# app.py
from fastapi import FastAPI, Request, Header
app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request, x_github_event: str = Header(None),
                  x_hub_signature_256: str = Header(None)):
    payload_bytes = await request.body()
    if not validate_github_signature(payload_bytes, x_hub_signature_256, WEBHOOK_SECRET):
        raise HTTPException(status_code=401)
    
    payload = await request.json()
    agent_name = router.route(x_github_event, payload)
    
    if agent_name != "ignore":
        # Run agent async so webhook returns fast
        background_tasks.add_task(dispatch_agent, agent_name, payload)
    
    return {"status": "ok"}

@app.get("/health")
async def health(): return {"status": "ok", "model": "gpt-5.5"}

@app.get("/repos/{owner}/{repo}/stats")
async def repo_stats(owner: str, repo: str):
    return await get_repo_stats(f"{owner}/{repo}")
```

---

## 12. Memory System

### Two-Layer Memory

```
Layer 1 — OpenAI Vector Store (semantic content)
  └── Full decision text, stored as files
  └── GPT-5.5 searches automatically via file_search tool
  └── No manual embedding code needed — OpenAI handles it

Layer 2 — Supabase (structured metadata)
  └── Memory refs, authors, dates, domains, file mappings
  └── Promise tracking
  └── Pattern rules
  └── Commit ledger
```

### Memory Document Format (Uploaded to Vector Store)

```
SAGE-MEMORY-042
TYPE: decision
DATE: 2024-09-15
AUTHOR: @senior-dev
SOURCE: PR #89
DOMAINS: auth, cache
FILES: src/auth/token_service.py, src/cache/redis_client.py
RISK: critical

DECISION:
Auth tokens must never be cached in Redis or any in-memory store.

REASONING:
On Sep 14 2024, the auth service went down for 2 hours because Redis cached
auth tokens without invalidating them on password reset. Users authenticated
with revoked credentials for 120 minutes. This is a critical security failure.

RULE:
Never cache auth responses. If caching is required for performance, cache only
non-sensitive metadata with TTL ≤ 30s and explicit invalidation on all auth events.
```

This format makes `file_search` extremely effective — it's rich, structured, and GPT-5.5 can reason about it.

---

## 13. CLI Tool

```bash
# Install
pip install -e .

# Commands
sage migrate --repo owner/repo --limit 500
sage validate --repo owner/repo
sage stats --repo owner/repo
sage dashboard --repo owner/repo --output ./sage-report.html
```

### `sage migrate` (Most Important CLI Command)

```python
@click.command()
@click.option("--repo", required=True)
@click.option("--limit", default=200)
def migrate(repo, limit):
    """Import past PRs retroactively into SAGE memory"""
    gh = Github(GITHUB_TOKEN)
    repo_obj = gh.get_repo(repo)
    prs = repo_obj.get_pulls(state="closed", sort="updated")
    
    vs_id = get_or_create_vector_store(repo)
    
    with click.progressbar(list(prs)[:limit]) as bar:
        for pr in bar:
            if pr.merged:
                # Run Decision Extractor logic offline
                run_decision_extractor_sync(repo, pr, vs_id)
    
    click.echo(f"Migration complete. Vector Store: {vs_id}")
```

---

## 14. Dashboard

Generated by `sage dashboard` or `@sage health`. Self-contained HTML file.

### Sections
1. **Overview Cards** — memory count, promise kept rate, pattern violations, risk breakdown
2. **Decision Graph** — Mermaid.js showing decision relationships and overrides
3. **Domain Coverage** — which domains are well-documented vs gaps
4. **Stale Decisions** — memories older than 1 year flagged for review
5. **Security Inventory** — all security decisions in one place
6. **Pattern Violation History** — which rules get broken most often
7. **Recent Timeline** — last 30 days of memory activity

---

## 15. Environment Variables

```bash
# .env

# OpenAI
OPENAI_API_KEY=sk-...              # Your $50 credits API key

# GitHub App
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY_PATH=./sage-app.pem
GITHUB_WEBHOOK_SECRET=your-secret-here
GITHUB_TOKEN=ghp_...               # For CLI tools

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...

# App
PORT=8000
ENVIRONMENT=development
MAX_DIFF_CHARS=80000               # Truncate massive diffs
MODEL=gpt-5.5                      # Switch to gpt-5.4-mini for dev/testing
```

### Cost Management with $50 Credits
- Use `gpt-5.4-mini` during development (much cheaper)
- Switch to `gpt-5.5` only for demo/production
- Set `MAX_DIFF_CHARS=80000` to avoid huge token bills on large PRs
- Vector Store file storage: ~$0.10/GB/day (negligible)

---

## 16. Build Phases

### Phase 1 — Core Loop (Days 1–4)
**Goal:** Issue → pre-mortem → PR review → extract decisions on merge

- [ ] FastAPI server + webhook receiver + HMAC validation
- [ ] GitHub App creation + JWT auth
- [ ] Supabase schema setup
- [ ] OpenAI Vector Store creation per repo
- [ ] Triage Router
- [ ] `store_memory` function tool (uploads to Vector Store + Supabase)
- [ ] Pre-Mortem Agent
- [ ] Decision Extractor Agent (needed to populate memory before review works)
- [ ] PR Review Agent (Layers 1 + 2 first)
- [ ] GitHub comment posting

**Milestone:** Open issue → get pre-mortem → open PR → get review → merge → see decision stored

---

### Phase 2 — Full Review + Reply Loop (Days 5–7)
**Goal:** All 5 PR review layers + developer reply flow working

- [ ] PR Review Layers 3 (web_search for CVEs), 4, 5
- [ ] Active patterns stored + fetched + enforced
- [ ] Reply Handler (`sage: intentional / accidental / discuss`)
- [ ] Memory override flow (old memory marked, new one created)
- [ ] Follow-Up Agent (evaluates developer's issue replies)
- [ ] Promise verification working end-to-end

**Milestone:** Full `sage: intentional` → memory evolution cycle working

---

### Phase 3 — Power Agents (Days 8–10)
**Goal:** Complete agent roster

- [ ] SAGE Ask (`@sage ask "question"`)
- [ ] Onboarding Agent (`@sage onboard @user`)
- [ ] Commit Keeper (push → ledger)
- [ ] Health Auditor (`@sage health`)
- [ ] Basic HTML dashboard generation

**Milestone:** New dev can `@sage onboard @them` and get a full briefing

---

### Phase 4 — CLI + Polish (Days 11–13)
**Goal:** Production-grade tooling

- [ ] `sage migrate` — retroactive import of past PRs
- [ ] `sage validate` — memory integrity checks
- [ ] `sage stats` — JSON summary
- [ ] `sage dashboard` — full HTML with Mermaid graphs
- [ ] Error handling + retry logic (3 retries, exponential backoff)
- [ ] Rate limiting on webhook endpoint
- [ ] Full test suite (target: 50+ tests)

**Milestone:** Run `sage migrate` on a real 100-PR repo

---

### Phase 5 — Differentiators (Hackathon Bonus)
- [ ] Cross-repo memory sharing (org-level decisions)
- [ ] Memory confidence decay visualization
- [ ] ADR export (generate markdown ADR files from memories)
- [ ] Slack bridge for `@sage ask`
- [ ] VS Code extension showing decisions while coding

---

## 17. Testing Plan

```python
# tests/test_pr_review.py
async def test_catches_semantic_equivalent_pattern():
    """PR with in-memory dict cache triggers memory about Redis auth caching"""

async def test_promise_verification_catches_broken_ttl():
    """Issue promised 30s TTL, PR has 1800s → flagged as broken"""

async def test_security_layer_catches_weak_hashing():
    """MD5 usage in PR → flagged by security layer"""

async def test_pattern_enforcement_applies_reviewer_rule():
    """Stored pattern 'no sync Redis in async' triggers on matching diff"""

async def test_web_search_looks_up_cve():
    """New dependency added → web_search called for CVE lookup"""

# tests/test_memory_vector_store.py
async def test_store_and_retrieve_decision():
    """Store decision, search for it, verify it comes back"""

async def test_semantic_search_finds_equivalent_pattern():
    """Query about 'token storage' finds memory about 'auth caching'"""

# tests/test_reply_handler.py
async def test_intentional_override_updates_memory():
    """sage: intentional → old memory overridden, new one created"""

async def test_discuss_tags_original_authors():
    """sage: discuss → original decision makers tagged in comment"""

# tests/test_cli_migrate.py
def test_migrate_imports_decisions_from_past_prs():
    """sage migrate on test repo with 20 PRs → decisions stored"""
```

---

## 18. Deployment

### GitHub Actions CI/CD

```yaml
# .github/workflows/ci.yml
name: SAGE CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
      SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with: {python-version: '3.11'}
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --tb=short

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Railway
        run: railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

### Railway Deploy

```bash
npm install -g @railway/cli
railway login
railway init
railway up

# Set secrets
railway variables set OPENAI_API_KEY=sk-...
railway variables set GITHUB_APP_ID=...
railway variables set GITHUB_WEBHOOK_SECRET=...
railway variables set SUPABASE_URL=...
railway variables set SUPABASE_SERVICE_KEY=...
```

---

## 19. Credit Usage Estimate

You have **$50 free trial credits**. Here's how to manage them:

| Activity | Model | Est. Cost Per Call | Notes |
|---|---|---|---|
| Pre-Mortem | gpt-5.5 | ~$0.05 | Rich context + file_search |
| PR Review (5 layers) | gpt-5.5 | ~$0.15 | Largest prompt, diff + memory |
| Decision Extractor | gpt-5.5 | ~$0.08 | All PR comments + diff |
| SAGE Ask | gpt-5.5 | ~$0.03 | Shorter interaction |
| Commit Keeper | gpt-5.4-mini | ~$0.002 | Keep this cheap |
| `sage migrate` (100 PRs) | gpt-5.5 | ~$8.00 | Run once carefully |

**Budget strategy:**
- Dev/testing: use `gpt-5.4-mini` (set `MODEL=gpt-5.4-mini` in .env)
- Demo flows: use `gpt-5.5`
- Your $50 = comfortable runway for hackathon dev + demo

---

## 20. Differentiators Over LORE

| Feature | LORE (GitLab) | SAGE (GitHub) |
|---|---|---|
| Platform | GitLab only | GitHub (10x larger) |
| Memory storage | Wiki pages (text) | OpenAI Vector Stores (true semantic) |
| LLM | Claude | **GPT-5.5 (native Codex model)** |
| Security layer | Claude reasoning | GPT-5.5 + **live web_search for CVEs** |
| Code analysis | Prompt only | **code_interpreter on actual diffs** |
| Agent behavior | Prompt-chained | **GPT-5.5 autonomously calls tools** |
| Stale decisions | No | Yes — flag outdated memories |
| Cross-repo memory | No | Yes — org-level shared decisions |
| ADR export | No | Yes — export as markdown ADR files |
| Promise tracking | Yes | Yes + verified on next push |
| Memory override | Yes | Yes + full audit trail |
| Context window | Standard | **1M tokens — entire repo history** |

---

## Quick Start Checklist (Do This in Order)

```
Day 1:  pip install, create GitHub App, set up Supabase schema, create .env
Day 2:  FastAPI server + webhook validation + GitHub JWT auth working
        Test: curl your /webhook endpoint, see it parse a fake payload
Day 3:  OpenAI Vector Store creation + store_memory tool working
        Test: store one decision, verify it appears in OpenAI dashboard
Day 4:  Pre-Mortem Agent end-to-end
        Test: open a real issue on a test repo, see SAGE comment
Day 5:  Decision Extractor (populate memory before review works)
        Test: merge a test PR, see decisions stored in Vector Store
Day 6:  PR Review Agent Layer 1 + 2 (memory conflicts + promises)
        Test: open PR that conflicts with stored decision, see it caught
Day 7:  PR Review Layers 3 (web_search CVEs), 4, 5 (patterns)
        Test: add new npm package to PR, see CVE search in action
Day 8:  Reply Handler (sage: intentional/accidental/discuss)
        Test: comment sage: intentional, see memory updated
Day 9:  Follow-Up + SAGE Ask + Commit Keeper
Day 10: Onboarding + Health Auditor + basic dashboard
Day 11: sage migrate CLI command
Day 12: Full dashboard + sage validate + sage stats
Day 13: Tests, tests, tests. Fix everything.
Day 14: Deploy to Railway, point GitHub App webhook, demo on real repo
```

---

*SAGE — Built for the Codex Hackathon. Powered by GPT-5.5.*
*Your GitHub repo deserves a memory.*
