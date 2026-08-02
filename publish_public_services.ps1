[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$env:PYTHONPATH = (Resolve-Path '.\backend').Path

$databaseUrlWasProvided = -not [string]::IsNullOrWhiteSpace($env:DATABASE_URL)
if (-not $databaseUrlWasProvided) {
    $secureUrl = Read-Host -Prompt 'Supabase Session Pooler URI' -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureUrl)
    try {
        $env:DATABASE_URL = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

try {
    python -m app.cli.publish_public_services
    if ($LASTEXITCODE -ne 0) {
        throw "Public-service publishing failed with exit code $LASTEXITCODE."
    }
}
finally {
    if (-not $databaseUrlWasProvided) {
        Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
    }
}
