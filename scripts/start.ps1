# Sports Video Logger - Windows launcher (Python)
$ErrorActionPreference = 'Stop'

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $ProjectRoot

function Write-Info($text) {
    Write-Host $text -ForegroundColor Cyan
}

function Write-Err($text) {
    Write-Host $text -ForegroundColor Red
}

Write-Info '=== Sports Video Logger ==='
Write-Info "Project: $ProjectRoot"
Write-Host ''

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Err 'Python not found. Install Python 3.11+ from https://www.python.org/'
    exit 1
}

if (-not (Test-Path '.venv')) {
    Write-Info 'First run: creating virtual environment (.venv)...'
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Err 'Failed to create virtual environment.'
        exit $LASTEXITCODE
    }
    Write-Host ''
}

& ".\.venv\Scripts\Activate.ps1"

Write-Info 'Installing/updating dependencies...'
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Err 'pip install failed.'
    exit $LASTEXITCODE
}

Write-Info 'Starting Flask server...'
Write-Host 'Open http://127.0.0.1:5000 in browser. Stop with Ctrl+C.'
Write-Host ''

python -m backend.app
exit $LASTEXITCODE
