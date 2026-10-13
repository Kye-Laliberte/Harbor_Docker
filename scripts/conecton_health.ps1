$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repositoryRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repositoryRoot

try {
    $envPath = Join-Path $repositoryRoot ".env"
    if (-not (Test-Path -LiteralPath $envPath)) {
        throw "Missing .env. Create it with API_KEY and the Docker database settings."
    }

    $apiKeyLine = Get-Content -LiteralPath $envPath |
        Where-Object { $_ -match '^\s*API_KEY\s*=' } |
        Select-Object -First 1
    if ($null -eq $apiKeyLine -or $apiKeyLine -notmatch '^\s*API_KEY\s*=\s*(.*?)\s*$') {
        throw ".env must define API_KEY."
    }

    $apiKey = $Matches[1]
    if ($apiKey.Length -ge 2 -and
        (($apiKey.StartsWith('"') -and $apiKey.EndsWith('"')) -or
         ($apiKey.StartsWith("'") -and $apiKey.EndsWith("'")))) {
        $apiKey = $apiKey.Substring(1, $apiKey.Length - 2)
    }
    if ([string]::IsNullOrWhiteSpace($apiKey)) {
        throw ".env must define a non-empty API_KEY."
    }

    & docker compose exec -T postgres pg_isready
    if ($LASTEXITCODE -ne 0) {
        throw "Database connection check failed. Start the stack with 'docker compose up -d api' and check the Postgres logs."
    }
    Write-Host "[OK] PostgreSQL is accepting connections"

    $apiUri = "http://localhost:8000/ships/list"
    $response = Invoke-WebRequest `
        -Uri $apiUri `
        -Method Get `
        -Headers @{ "X-API-Key" = $apiKey } `
        -TimeoutSec 10 `
        -UseBasicParsing
    if ($response.StatusCode -ne 200) {
        throw "Authenticated API check returned HTTP $($response.StatusCode)."
    }
    Write-Host "[OK] Authenticated API/database request ($apiUri)"
}
finally {
    $apiKey = $null
    Pop-Location
}
