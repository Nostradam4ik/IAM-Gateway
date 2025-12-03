#requires -Version 5.1
param(
    [switch]$Recreate
)

$ErrorActionPreference = "Stop"
$composeFile = Join-Path $PSScriptRoot "..\docker\docker-compose.midpoint.yml"

if (-not (Test-Path $composeFile)) {
    throw "docker-compose file not found: $composeFile"
}

Write-Host "Starting MidPoint stack..." -ForegroundColor Cyan
if ($Recreate) {
    docker compose -f $composeFile down --remove-orphans
}

docker compose -f $composeFile up -d

Write-Host ""
Write-Host "Services launched:" -ForegroundColor Green
Write-Host "  MidPoint UI     -> http://localhost:8080/midpoint (admin/admin)"
Write-Host "  ApacheDS LDAP   -> ldap://localhost:10389 (admin=cn=admin,dc=example,dc=com)"
Write-Host "  Odoo            -> http://localhost:8069"
Write-Host "  Intranet DB     -> postgres://intranet:intranet@localhost:55432/intranet"

Write-Host ""
Write-Host "To stop the stack run:" -ForegroundColor Yellow
Write-Host "  docker compose -f $composeFile down"

