<#
.SYNOPSIS
    Run smoke_test.py for every demo in this repo against the live Foundry
    deployment. Use as a dress-rehearsal before showtime.

.DESCRIPTION
    For each demo folder (01-..05-):
      1. Create .venv if it doesn't exist
      2. pip install -r requirements.txt (cached after first run)
      3. Run smoke_test.py

    Prints a green/red summary at the end.

.PARAMETER Only
    Comma-separated demo numbers to run, e.g. -Only 1,3,5

.PARAMETER SkipInstall
    Skip the pip install step (assume venvs are already up to date).

.PARAMETER ContinueOnFailure
    Keep running subsequent demos even if one fails.

.EXAMPLE
    .\run_all_demos.ps1

.EXAMPLE
    .\run_all_demos.ps1 -Only 1,4 -SkipInstall

.NOTES
    Requires: Python 3.10+, az login, and a .env in each demo folder.
#>
[CmdletBinding()]
param(
    [string]$Only = '',
    [switch]$SkipInstall,
    [switch]$ContinueOnFailure
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

$demos = @(
    @{ Num = 1; Folder = '01-basic-agent-tools';     Script = 'smoke_test.py' }
    @{ Num = 2; Folder = '02-agent-knowledge';       Script = 'smoke_test.py' }
    @{ Num = 3; Folder = '03-mcp-tool-server';       Script = 'smoke_test.py' }
    @{ Num = 4; Folder = '04-evaluations-security';  Script = 'smoke_test.py' }
    @{ Num = 5; Folder = '05-production-readiness';  Script = 'smoke_test.py' }
)

if ($Only) {
    $wanted = $Only.Split(',') | ForEach-Object { [int]$_.Trim() }
    $demos = $demos | Where-Object { $wanted -contains $_.Num }
}

# Pre-flight: az login check
Write-Host "==> Pre-flight: az account show" -ForegroundColor Cyan
try {
    $acct = (az account show --output json | ConvertFrom-Json)
    Write-Host "    subscription: $($acct.name) ($($acct.id))" -ForegroundColor Gray
} catch {
    Write-Host "    FAILED. Run 'az login' first." -ForegroundColor Red
    exit 2
}

$results = @()

foreach ($demo in $demos) {
    $folder  = Join-Path $repoRoot $demo.Folder
    $venv    = Join-Path $folder '.venv'
    $reqs    = Join-Path $folder 'requirements.txt'
    $envFile = Join-Path $folder '.env'
    $script  = Join-Path $folder $demo.Script

    Write-Host ''
    Write-Host ("==> Demo {0}: {1}" -f $demo.Num, $demo.Folder) -ForegroundColor Cyan

    if (-not (Test-Path $envFile)) {
        Write-Host "    .env missing -- skipping" -ForegroundColor Yellow
        $results += [PSCustomObject]@{ Num=$demo.Num; Folder=$demo.Folder; Status='SKIPPED'; Detail='no .env' }
        continue
    }

    # Set up venv if missing
    if (-not (Test-Path $venv)) {
        Write-Host "    creating venv..." -ForegroundColor Gray
        python -m venv $venv
    }

    $activate = Join-Path $venv 'Scripts\Activate.ps1'
    . $activate

    if (-not $SkipInstall) {
        Write-Host "    pip install -q -r requirements.txt..." -ForegroundColor Gray
        pip install -q -r $reqs
    }

    # Run the smoke test
    $env:PYTHONIOENCODING = 'utf-8'
    Push-Location $folder
    $start = Get-Date
    try {
        python $demo.Script
        $exitCode = $LASTEXITCODE
    } finally {
        Pop-Location
    }
    $duration = [int]((Get-Date) - $start).TotalSeconds

    if ($exitCode -eq 0) {
        Write-Host ("    PASSED in {0}s" -f $duration) -ForegroundColor Green
        $results += [PSCustomObject]@{ Num=$demo.Num; Folder=$demo.Folder; Status='PASSED'; Detail="${duration}s" }
    } else {
        Write-Host ("    FAILED in {0}s (exit {1})" -f $duration, $exitCode) -ForegroundColor Red
        $results += [PSCustomObject]@{ Num=$demo.Num; Folder=$demo.Folder; Status='FAILED'; Detail="exit ${exitCode}" }
        if (-not $ContinueOnFailure) {
            Write-Host '    Stopping. Re-run with -ContinueOnFailure to keep going.' -ForegroundColor Yellow
            break
        }
    }
}

Write-Host ''
Write-Host '==> Summary' -ForegroundColor Cyan
$results | Format-Table -AutoSize

$failed = @($results | Where-Object { $_.Status -eq 'FAILED' }).Count
if ($failed -gt 0) {
    exit 1
}
exit 0
