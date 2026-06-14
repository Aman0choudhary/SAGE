# SAGE

SAGE is a GitHub App that gives repositories durable decision memory. It receives
GitHub webhooks, routes them to agent workflows, lets OpenAI Responses API agents
use tools, and stores semantic memories in OpenAI Vector Stores with structured
metadata in Supabase.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
copy .env.example .env
uvicorn sage.app:app --reload
```

Run tests:

```bash
python -m pytest
```

## Current build slice

- FastAPI webhook endpoint with HMAC validation
- GitHub event router
- GitHub App installation-token auth with `GITHUB_TOKEN` fallback
- Live GitHub PR diff/comment fetching for PR review and decision extraction
- OpenAI Responses API agent loop with function-call outputs
- Tool definitions and handler dispatch
- In-memory development store plus Supabase/OpenAI integration points
- Phase 1 agents and command agents scaffolded
- CLI skeleton for `sage stats`, `sage validate`, `sage dashboard`, and `sage migrate`

## What you need to do

1. Create a GitHub App:
   - Webhook URL: `https://YOUR_PUBLIC_URL/webhook`
   - Webhook secret: copy into `GITHUB_WEBHOOK_SECRET`
   - Repository permissions: Issues read/write, Pull requests read/write, Contents read, Metadata read
   - Events: Issues, Issue comments, Pull requests, Pull request review comments, Push
   - Download the private key and set either `GITHUB_APP_PRIVATE_KEY_PATH` or `GITHUB_APP_PRIVATE_KEY`

2. Create a Supabase project:
   - Run `schema.sql` in the SQL editor
   - Set `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`

3. Add OpenAI credentials:
   - Set `OPENAI_API_KEY`
   - Keep `MODEL=gpt-5.5` for the hackathon demo, or set your cheaper dev model while testing

4. Expose the local app while developing:
   - Start the server with `uvicorn sage.app:app --reload`
   - Use a tunnel such as ngrok or Cloudflare Tunnel and paste its `/webhook` URL into the GitHub App

5. Install the GitHub App on your test repo, then try:
   - Open an issue to trigger the pre-mortem agent
   - Open a PR to trigger PR review
   - Merge a PR to trigger decision extraction

6. For CLI migration:
   - Set `GITHUB_TOKEN` with repo read access
   - Run `sage migrate --repo owner/repo --limit 50`
