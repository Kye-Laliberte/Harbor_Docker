$ErrorActionPreference = "Stop"

if (-not (Test-Path ".env")) {
    throw "Create a .env file with API_KEY and the Docker database settings before running API tests."
}

if (-not (Select-String -Path ".env" -Pattern '^\s*API_KEY\s*=\s*.+$' -Quiet)) {
    throw "The .env file must define a non-empty API_KEY."
}

& docker compose up --build -d api
if ($LASTEXITCODE -ne 0) {
    throw "Failed to start the Docker API stack."
}

& docker compose exec -T api alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    throw "Database migrations failed."
}

& docker compose --profile test run --rm postman-tests
if ($LASTEXITCODE -ne 0) {
    throw "Postman/Newman API tests failed."
}