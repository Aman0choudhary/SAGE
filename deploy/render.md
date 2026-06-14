# Deploy SAGE to Render

Render is the simplest no-Docker option because it can deploy directly from the
GitHub repo.

## 1. Create service

1. Go to Render.
2. New -> Web Service.
3. Connect `Aman0choudhary/SAGE`.
4. Runtime: Python.
5. Build command:

```bash
pip install -r requirements.txt
```

6. Start command:

```bash
python -m uvicorn sage.app:app --host 0.0.0.0 --port $PORT
```

## 2. Environment variables

Set these in Render dashboard:

```text
OPENAI_API_KEY
MODEL=gpt-5.5
GITHUB_APP_ID
GITHUB_APP_PRIVATE_KEY
GITHUB_WEBHOOK_SECRET
GITHUB_TOKEN
GITHUB_API_URL=https://api.github.com
SUPABASE_URL
SUPABASE_SERVICE_KEY
ENVIRONMENT=production
MAX_DIFF_CHARS=80000
```

For `GITHUB_APP_PRIVATE_KEY`, paste the full contents of `sage-app.pem`.

Do not use `GITHUB_APP_PRIVATE_KEY_PATH` on Render.

## 3. Update GitHub App webhook

Set webhook URL to:

```text
https://YOUR_RENDER_SERVICE.onrender.com/webhook
```

Then open an issue in the installed repo.

