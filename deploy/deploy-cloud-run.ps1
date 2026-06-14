param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Region = "asia-south1",
    [string]$ServiceName = "sage"
)

$ErrorActionPreference = "Stop"
if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$gcloud = Get-Command gcloud -ErrorAction SilentlyContinue
if (-not $gcloud) {
    $candidate = "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
    if (Test-Path $candidate) {
        $gcloud = $candidate
    } else {
        throw "gcloud was not found. Install Google Cloud SDK or open a new PowerShell window."
    }
} else {
    $gcloud = $gcloud.Source
}

function Read-DotEnv {
    param([string]$Path)
    $values = @{}
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
            return
        }
        $parts = $line.Split("=", 2)
        $key = $parts[0].Trim()
        $value = $parts[1].Trim().Trim('"').Trim("'")
        $values[$key] = $value
    }
    return $values
}

function Set-Secret {
    param(
        [string]$Name,
        [string]$Value
    )
    if (-not $Value) {
        throw "Missing secret value for $Name"
    }

    $null = & $gcloud secrets describe $Name --project $ProjectId --format="value(name)" 2>$null
    $exists = $LASTEXITCODE -eq 0

    $tempFile = New-TemporaryFile
    $tempPath = $tempFile.FullName
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($tempPath, $Value, $utf8NoBom)

    try {
        if (-not $exists) {
            & $gcloud secrets create $Name --project $ProjectId --data-file=$tempPath
        } else {
            & $gcloud secrets versions add $Name --project $ProjectId --data-file=$tempPath
        }
    } finally {
        Remove-Item -LiteralPath $tempPath -Force -ErrorAction SilentlyContinue
    }
}

$envPath = Join-Path $repoRoot ".env"
if (-not (Test-Path $envPath)) {
    throw ".env not found at $envPath"
}

$values = Read-DotEnv $envPath

$privateKey = $values["GITHUB_APP_PRIVATE_KEY"]
if (-not $privateKey) {
    $keyPath = $values["GITHUB_APP_PRIVATE_KEY_PATH"]
    if (-not $keyPath) {
        throw "Set GITHUB_APP_PRIVATE_KEY or GITHUB_APP_PRIVATE_KEY_PATH in .env"
    }
    $resolvedKeyPath = Resolve-Path -Path $keyPath
    $privateKey = Get-Content -Raw -Path $resolvedKeyPath
}

& $gcloud config set project $ProjectId
& $gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com --project $ProjectId

$projectNumber = & $gcloud projects describe $ProjectId --format="value(projectNumber)"
$runtimeServiceAccount = "$projectNumber-compute@developer.gserviceaccount.com"
& $gcloud projects add-iam-policy-binding $ProjectId `
    --member "serviceAccount:$runtimeServiceAccount" `
    --role "roles/secretmanager.secretAccessor" `
    --quiet

Set-Secret "OPENAI_API_KEY" $values["OPENAI_API_KEY"]
Set-Secret "GITHUB_APP_PRIVATE_KEY" $privateKey
Set-Secret "GITHUB_WEBHOOK_SECRET" $values["GITHUB_WEBHOOK_SECRET"]
Set-Secret "GITHUB_TOKEN" $values["GITHUB_TOKEN"]
Set-Secret "SUPABASE_SERVICE_KEY" $values["SUPABASE_SERVICE_KEY"]

$plainEnv = @(
    "MODEL=$($values['MODEL'])",
    "ENVIRONMENT=production",
    "MAX_DIFF_CHARS=$($values['MAX_DIFF_CHARS'])",
    "SUPABASE_URL=$($values['SUPABASE_URL'])",
    "GITHUB_APP_ID=$($values['GITHUB_APP_ID'])",
    "GITHUB_API_URL=$($values['GITHUB_API_URL'])"
) -join ","

$secretEnv = "OPENAI_API_KEY=OPENAI_API_KEY:latest,GITHUB_APP_PRIVATE_KEY=GITHUB_APP_PRIVATE_KEY:latest,GITHUB_WEBHOOK_SECRET=GITHUB_WEBHOOK_SECRET:latest,GITHUB_TOKEN=GITHUB_TOKEN:latest,SUPABASE_SERVICE_KEY=SUPABASE_SERVICE_KEY:latest"

& $gcloud run deploy $ServiceName `
    --source . `
    --region $Region `
    --allow-unauthenticated `
    --set-env-vars $plainEnv `
    --set-secrets $secretEnv `
    --project $ProjectId `
    --quiet

& $gcloud run services describe $ServiceName `
    --region $Region `
    --project $ProjectId `
    --format="value(status.url)"
