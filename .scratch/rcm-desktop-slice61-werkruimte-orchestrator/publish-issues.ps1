# Publish slice 61 issues to GitHub (requires: gh auth login)
# Run from repo root: .\.scratch\rcm-desktop-slice61-werkruimte-orchestrator\publish-issues.ps1

$ErrorActionPreference = "Stop"
$base = Join-Path $PSScriptRoot "issues"
$label = "ready-for-agent"
$repo = "ReinderRoos/rcm-desktop"

$ghCmd = Get-Command gh -ErrorAction SilentlyContinue
if (-not $ghCmd) {
    $ghExe = Join-Path ${env:ProgramFiles} "GitHub CLI\gh.exe"
    if (-not (Test-Path $ghExe)) {
        throw "GitHub CLI (gh) not found. Install via: winget install GitHub.cli"
    }
    $ghCmd = $ghExe
}

function Invoke-Gh {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    if ($ghCmd -is [string]) {
        & $ghCmd @Args
    } else {
        & $ghCmd.Source @Args
    }
    if ($LASTEXITCODE -ne 0) { throw "gh failed: $($Args -join ' ')" }
}

if (-not $env:GH_TOKEN) {
    $authCheck = if ($ghCmd -is [string]) { & $ghCmd auth status 2>&1 } else { & $ghCmd.Source auth status 2>&1 }
    if ($LASTEXITCODE -ne 0) {
        throw @"
GitHub CLI is not authenticated.
Run once in your terminal:
  gh auth login
Or set GH_TOKEN, then rerun this script.
"@
    }
}

function New-GhIssue {
    param([string]$Title, [string]$BodyFile)
    Invoke-Gh issue create --repo $repo --title $Title --body-file $BodyFile --label $label
}

Write-Host "Creating parent issue..."
$parentUrl = New-GhIssue -Title 'Slice 61 - ResultsWorkspaceOrchestrator (parent)' -BodyFile (Join-Path $base "gh-parent.md")
Write-Host "Parent: $parentUrl"

function Set-ParentUrl {
    param([string]$File)
    $content = Get-Content $File -Raw
    $content = $content -replace "PARENT_ISSUE_URL", $parentUrl
    Set-Content $File -Value $content -NoNewline
}

Set-ParentUrl (Join-Path $base "gh-01.md")
Set-ParentUrl (Join-Path $base "gh-02.md")
Set-ParentUrl (Join-Path $base "gh-03.md")

Write-Host "Creating child 01..."
$child01Url = New-GhIssue -Title 'Slice 61-01 - UiSync-plan voor resultatenwerkruimte' -BodyFile (Join-Path $base "gh-01.md")
Write-Host "Child 01: $child01Url"

$content02 = Get-Content (Join-Path $base "gh-02.md") -Raw
$content02 = $content02 -replace "CHILD_01_ISSUE_URL", $child01Url
$tmp02 = Join-Path $base "gh-02-publish.md"
Set-Content $tmp02 -Value $content02 -NoNewline

Write-Host "Creating child 02..."
$child02Url = New-GhIssue -Title 'Slice 61-02 - Render-plan voor resultatenwerkruimte' -BodyFile $tmp02
Write-Host "Child 02: $child02Url"
Remove-Item $tmp02 -ErrorAction SilentlyContinue

$content03 = Get-Content (Join-Path $base "gh-03.md") -Raw
$content03 = $content03 -replace "CHILD_02_ISSUE_URL", $child02Url
$tmp03 = Join-Path $base "gh-03-publish.md"
Set-Content $tmp03 -Value $content03 -NoNewline

Write-Host "Creating child 03..."
$child03Url = New-GhIssue -Title 'Slice 61-03 - Orchestrator gates en view cleanup' -BodyFile $tmp03
Write-Host "Child 03: $child03Url"
Remove-Item $tmp03 -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Done. Issue URLs:"
Write-Host "  Parent: $parentUrl"
Write-Host "  01:     $child01Url"
Write-Host "  02:     $child02Url"
Write-Host "  03:     $child03Url"
Write-Host ""
Write-Host "Update local issue files with these URLs, then start implementation on child 01."
