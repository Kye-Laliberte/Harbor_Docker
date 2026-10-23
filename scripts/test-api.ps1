
# Check if the .env file exists
$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $repoRoot ".env"
if (-not (Test-Path $envFile)) {
    throw "Create a .env file with API_KEY and the Docker database settings before running API tests."
}
if (-not (Select-String -Path $envFile -Pattern '^\s*API_KEY\s*=\s*.+$' -Quiet)) {
    throw "The .env file must define a non-empty API_KEY."
}

$composeProject = "harbor-postman-test-$PID"
$composeArgs = @("--project-name", $composeProject, "--profile", "test")
$testExitCode = 1
$cleanupExitCode = 0

Push-Location $repoRoot
try {
    & docker compose @composeArgs up --build --detach postman-postgres postman-api
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to start the isolated Postman test API and database."
    }

    & docker compose @composeArgs run --rm postman-tests
    $testExitCode = $LASTEXITCODE
}
finally {
    try {
        & docker compose @composeArgs down --remove-orphans
        $cleanupExitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
}

if ($cleanupExitCode -ne 0) {
    throw "Failed to remove the isolated Postman test stack."
}
exit $testExitCode
