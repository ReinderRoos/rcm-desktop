# Publish slice 71 issues to GitHub (requires: gh auth login)
# Run from repo root:
#   .\.scratch\rcm-desktop-slice71-nb-effectfilter-workspace-ux\publish-issues.ps1

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

function Publish-Child {
    param(
        [string]$Title,
        [string]$BodyFile,
        [hashtable]$Replacements
    )
    $content = Get-Content $BodyFile -Raw
    foreach ($key in $Replacements.Keys) {
        $content = $content -replace [regex]::Escape($key), $Replacements[$key]
    }
    $tmp = Join-Path $base ("publish-" + [guid]::NewGuid().Guid + ".md")
    Set-Content $tmp -Value $content -NoNewline
    try {
        return (New-GhIssue -Title $Title -BodyFile $tmp)
    } finally {
        Remove-Item $tmp -ErrorAction SilentlyContinue
    }
}

Write-Host "Creating parent issue..."
$parentUrl = New-GhIssue -Title "Slice 71 - NB-effectfilter & workspace UX (parent)" -BodyFile (Join-Path $base "gh-parent.md")
Write-Host "Parent: $parentUrl"

Get-ChildItem (Join-Path $base "gh-*.md") | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    $content = $content -replace "PARENT_ISSUE_URL", $parentUrl
    Set-Content $_.FullName -Value $content -NoNewline
}

Write-Host "Creating child 00..."
$child00Url = Publish-Child -Title "Slice 71-00 - Lifecycle-kosten regressie CM-overlay" -BodyFile (Join-Path $base "gh-00.md") -Replacements @{}
Write-Host "Child 00: $child00Url"

Write-Host "Creating child 01..."
$child01Url = Publish-Child -Title "Slice 71-01 - EffectNbFilterSet + NB-seam EffectImpactService" -BodyFile (Join-Path $base "gh-01.md") -Replacements @{ "CHILD_00_ISSUE_URL" = $child00Url }
Write-Host "Child 01: $child01Url"

Write-Host "Creating child 02..."
$child02Url = Publish-Child -Title "Slice 71-02 - Gefilterde Top 10 aggregatie" -BodyFile (Join-Path $base "gh-02.md") -Replacements @{ "CHILD_01_ISSUE_URL" = $child01Url }
Write-Host "Child 02: $child02Url"

Write-Host "Creating child 03..."
$child03Url = Publish-Child -Title "Slice 71-03 - Workspace state + verwijder hybrid UX" -BodyFile (Join-Path $base "gh-03.md") -Replacements @{ "CHILD_02_ISSUE_URL" = $child02Url }
Write-Host "Child 03: $child03Url"

Write-Host "Creating child 08 (parallel pad na 03)..."
$child08Url = Publish-Child -Title "Slice 71-08 - Functierapport smoke" -BodyFile (Join-Path $base "gh-08.md") -Replacements @{ "CHILD_03_ISSUE_URL" = $child03Url }
Write-Host "Child 08: $child08Url"

Write-Host "Creating child 04..."
$child04Url = Publish-Child -Title "Slice 71-04 - Top 10 UI metric 3-way + NB-effectfilter" -BodyFile (Join-Path $base "gh-04.md") -Replacements @{ "CHILD_03_ISSUE_URL" = $child03Url }
Write-Host "Child 04: $child04Url"

Write-Host "Creating child 05..."
$child05Url = Publish-Child -Title "Slice 71-05 - NB-jaarreeks + Tijdsplot dataseam" -BodyFile (Join-Path $base "gh-05.md") -Replacements @{
    "CHILD_01_ISSUE_URL" = $child01Url
    "CHILD_03_ISSUE_URL" = $child03Url
}
Write-Host "Child 05: $child05Url"

Write-Host "Creating child 06..."
$child06Url = Publish-Child -Title "Slice 71-06 - Tijdsplot UI gedeelde metric + NB-curve" -BodyFile (Join-Path $base "gh-06.md") -Replacements @{ "CHILD_05_ISSUE_URL" = $child05Url }
Write-Host "Child 06: $child06Url"

Write-Host "Creating child 07..."
$child07Url = Publish-Child -Title "Slice 71-07 - Regressie, CONTEXT.md, test-migratie" -BodyFile (Join-Path $base "gh-07.md") -Replacements @{
    "CHILD_04_ISSUE_URL" = $child04Url
    "CHILD_05_ISSUE_URL" = $child05Url
    "CHILD_06_ISSUE_URL" = $child06Url
}
Write-Host "Child 07: $child07Url"

Write-Host ""
Write-Host "Done. Issue URLs:"
Write-Host "  Parent: $parentUrl"
Write-Host "  00:     $child00Url  <- start here"
Write-Host "  01:     $child01Url"
Write-Host "  02:     $child02Url"
Write-Host "  03:     $child03Url"
Write-Host "  04:     $child04Url"
Write-Host "  05:     $child05Url"
Write-Host "  06:     $child06Url"
Write-Host "  07:     $child07Url"
Write-Host "  08:     $child08Url"
Write-Host ""
Write-Host "Update issues/INDEX.md and local NN.md files with GitHub URLs."
