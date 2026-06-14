# SAGE - Semantic Agentic Git Engine

<p align="center">
  <img src="assets/sage-logo.png" alt="SAGE Semantic Agentic Git Engine logo" width="100%">
</p>

SAGE gives a GitHub repository memory. It is a GitHub App that watches issues,
pull requests, comments, merges, and pushes, then uses OpenAI's Responses API to
act like a senior engineer who remembers prior decisions.

When a risky issue or PR appears, SAGE can warn the team, ask hard questions,
track promises, review code against past decisions, and store new decisions for
future enforcement.

## Live Demo

- Cloud Run demo: https://s-age0-380815040698.europe-west1.run.app
- Demo video: https://youtu.be/atiNLq121zg
- Live proof issue: https://github.com/Aman0choudhary/SAGE/issues/9

<p align="center">
  <a href="https://youtu.be/atiNLq121zg">
    <img src="https://img.youtube.com/vi/atiNLq121zg/maxresdefault.jpg" alt="Watch the SAGE demo video" width="100%">
  </a>
</p>

## Demo Status

Working live loop:

```text
GitHub issue -> webhook -> FastAPI -> OpenAI Responses API -> GitHub bot comment + label
```

Verified locally:

- `23` tests passing
- GitHub webhook HMAC validation
- GitHub App bot comments and labels
- OpenAI API access with configured model
- Supabase metadata connectivity
- Cloudflare Tunnel local demo
- Cloud Run deployment files included

## Core Features

- Pre-mortem agent for newly opened issues
- Follow-up agent for developer replies
- PR review agent with five review layers
- Decision extractor for merged PRs
- Reply handler for `sage: intentional`, `sage: accidental`, and `sage: discuss`
- `@sage ask` memory Q&A agent
- Onboarding and health-audit agent scaffolds
- OpenAI Vector Store memory helper
- Supabase schema for structured metadata
- CLI commands for stats, validation, dashboard, and migration

## Architecture

```text
GitHub Webhooks
  -> FastAPI /webhook
  -> Router
  -> Agent
  -> OpenAI Responses API
  -> Function tools
  -> GitHub API + Supabase + OpenAI Vector Stores
```

Important folders:

```text
sage/app.py              FastAPI app
sage/router.py           GitHub event routing
sage/agents/             SAGE agents
sage/tools/              OpenAI function tool definitions and handlers
sage/github/             GitHub auth, comments, fetchers, webhooks
sage/memory/             Memory models, store, vector-store helper
sage/cli/                CLI commands
schema.sql               Supabase schema
deploy/                  Cloud Run and Render deployment guides
```

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .[dev]
Copy-Item .env.example .env
```

Fill `.env` with your real values. Do not commit `.env`.

Run the app:

```powershell
python -m uvicorn sage.app:app --reload
```

Health check:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health
```

Run tests:

```powershell
python -m pytest
```

## Environment Variables

Required:

```text
OPENAI_API_KEY
MODEL
GITHUB_APP_ID
GITHUB_WEBHOOK_SECRET
GITHUB_TOKEN
SUPABASE_URL
SUPABASE_SERVICE_KEY
PORT
ENVIRONMENT
MAX_DIFF_CHARS
```

For local GitHub App auth, use:

```text
GITHUB_APP_PRIVATE_KEY_PATH=./sage-app.pem
```

For cloud deployment, use:

```text
GITHUB_APP_PRIVATE_KEY=<full PEM contents>
```

Do not upload `sage-app.pem` to a cloud image or commit it to git.

## GitHub App Setup

Create a GitHub App with:

- Issues: read/write
- Pull requests: read/write
- Contents: read
- Metadata: read

Subscribe to:

- Issues
- Issue comments
- Pull requests
- Pull request review comments
- Push

Webhook URL:

```text
https://YOUR_PUBLIC_URL/webhook
```

The GitHub webhook secret must match `GITHUB_WEBHOOK_SECRET`.

## Try The Demo

Open a GitHub issue like:

```text
Title: Add Redis caching to auth token validation

Body: We want to cache auth token validation results for performance.
The implementation may cache revocation checks and token metadata.
```

Expected:

- SAGE bot comments with a pre-mortem
- SAGE applies a risk label such as `sage-risk: high`

Ask SAGE:

```text
@sage ask what should we know before caching auth tokens?
```

## Deployment

Deployment guides:

- Google Cloud Run: [deploy/cloud-run.md](deploy/cloud-run.md)
- Render: [deploy/render.md](deploy/render.md)

Cloud Run helper:

```powershell
.\deploy\deploy-cloud-run.ps1 -ProjectId YOUR_GCP_PROJECT_ID
```

After deployment, update the GitHub App webhook URL to:

```text
https://YOUR_DEPLOYED_URL/webhook
```

## Current Scope

This is a hackathon MVP. The live issue pre-mortem loop works. The PR review,
decision extraction, onboarding, health audit, and dashboard paths are scaffolded
and ready for deeper hardening.

Planned next steps:

- Full PR review end-to-end test
- Decision extraction after merge
- Rich dashboard
- Rate limiting and retries
- More integration tests
- ADR export and cross-repo memory
