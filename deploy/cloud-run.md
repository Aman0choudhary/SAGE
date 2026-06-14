# Deploy SAGE to Google Cloud Run

Cloud Run is the recommended production-ish demo target for SAGE.

## 1. Install and log in

Install the Google Cloud CLI:

```powershell
winget install --id Google.CloudSDK -e
```

Open a new PowerShell window, then:

```powershell
gcloud init
gcloud auth login
gcloud auth application-default login
```

## 2. Select project and enable services

```powershell
gcloud config set project YOUR_GCP_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
```

## 3. Create secrets

Use Secret Manager for real secrets. Do not commit `.env` or `.pem` files.

```powershell
gcloud secrets create OPENAI_API_KEY --data-file=- 
gcloud secrets create GITHUB_APP_PRIVATE_KEY --data-file=sage-app.pem
gcloud secrets create GITHUB_WEBHOOK_SECRET --data-file=-
gcloud secrets create GITHUB_TOKEN --data-file=-
gcloud secrets create SUPABASE_SERVICE_KEY --data-file=-
```

For commands using `--data-file=-`, paste the secret value, then press `Ctrl+Z`
and Enter in PowerShell.

Alternatively, after `gcloud init`, use the helper script from this repo:

```powershell
.\deploy\deploy-cloud-run.ps1 -ProjectId YOUR_GCP_PROJECT_ID
```

It reads your local `.env`, uploads secrets to Secret Manager, deploys to Cloud
Run, and prints the service URL.

## 4. Deploy from source

```powershell
gcloud run deploy sage `
  --source . `
  --region asia-south1 `
  --allow-unauthenticated `
  --set-env-vars MODEL=gpt-5.5,ENVIRONMENT=production,MAX_DIFF_CHARS=80000,SUPABASE_URL=https://YOUR_PROJECT.supabase.co,GITHUB_APP_ID=YOUR_GITHUB_APP_ID,GITHUB_API_URL=https://api.github.com `
  --set-secrets OPENAI_API_KEY=OPENAI_API_KEY:latest,GITHUB_APP_PRIVATE_KEY=GITHUB_APP_PRIVATE_KEY:latest,GITHUB_WEBHOOK_SECRET=GITHUB_WEBHOOK_SECRET:latest,GITHUB_TOKEN=GITHUB_TOKEN:latest,SUPABASE_SERVICE_KEY=SUPABASE_SERVICE_KEY:latest
```

Cloud Run prints a service URL like:

```text
https://sage-xxxxx-uc.a.run.app
```

## 5. Update GitHub App webhook

Set the GitHub App webhook URL to:

```text
https://YOUR_CLOUD_RUN_URL/webhook
```

The webhook secret in GitHub must exactly match `GITHUB_WEBHOOK_SECRET`.

## 6. Test

```powershell
Invoke-WebRequest https://YOUR_CLOUD_RUN_URL/health
```

Then open a GitHub issue in the installed repo. SAGE should comment and label it.
