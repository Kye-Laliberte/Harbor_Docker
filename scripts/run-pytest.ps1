param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PytestArgs
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $repoRoot ".env"
function Get-ApplicationDatabaseUrl{
    if ($env:DATABASE_URL) {
        return $env:DATABASE_URL
    }
    if (-not (Test-Path $envFile)){
        throw "DATABASE_URL is not set and .env was not found at $envFile."
    }
    foreach ($line in Get-Content $envFile) {
        if ($line -match '^\s*DATABASE_URL\s*=\s*(.*?)\s*$'){
            $value = $Matches[1]
            if ($value.Length -ge 2 -and
                (($value.StartsWith('"') -and $value.EndsWith('"')) -or
                 ($value.StartsWith("'") -and $value.EndsWith("'")))){
                $value = $value.Substring(1, $value.Length - 2)
            }
            return $value}
    }

    throw "DATABASE_URL was not found in .env."
}

$applicationDatabaseUrl = Get-ApplicationDatabaseUrl
try {
    $applicationUrl = [Uri]::new($applicationDatabaseUrl)
}
catch {
    throw "DATABASE_URL must be a valid PostgreSQL connection URL."
}

if ($applicationUrl.Scheme -notlike "postgresql*"){
    throw "DATABASE_URL must use PostgreSQL."
}
$applicationDatabase = [Uri]::UnescapeDataString(
    $applicationUrl.AbsolutePath.TrimStart("/")
)
$testDatabase = "harbor_test"
if (-not $applicationDatabase) {
    throw "DATABASE_URL must include the application database name."
}
if ($applicationDatabase -ieq $testDatabase){
    throw "The test database name must differ from the application database name."
}

$testUrl = [UriBuilder]::new($applicationUrl)
$testUrl.Path = "/$testDatabase"
if ($testUrl.Host -in @("postgres", "harbor-postgres", "localhost", "127.0.0.1")) {
    $testUrl.Host = "localhost"
    $testUrl.Port = 5432
}
$env:TEST_DATABASE_URL = $testUrl.Uri.AbsoluteUri

if (-not $PytestArgs -or $PytestArgs.Count -eq 0){
    $PytestArgs = @(
        "tests/test_harbor.py",
        "tests/test_dock.py",
        "tests/test_ship_endpoints.py",
        "-v")
}
Push-Location $repoRoot
try {
    python -m pytest @PytestArgs
    $pytestExitCode = $LASTEXITCODE
}
finally{
    Pop-Location
}
exit $pytestExitCode
