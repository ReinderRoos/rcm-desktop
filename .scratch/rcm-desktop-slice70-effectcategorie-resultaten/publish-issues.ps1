# Publish slice 70 issues to GitHub (requires: gh auth login)
# Run from repo root:
#   .\.scratch\rcm-desktop-slice70-effectcategorie-resultaten\publish-issues.ps1

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
$parentUrl = New-GhIssue -Title "Slice 70 - Effectcategorie-resultaten (parent)" -BodyFile (Join-Path $base "gh-parent.md")
Write-Host "Parent: $parentUrl"

$parentReplacements = @{ "PARENT_ISSUE_URL" = $parentUrl }
Get-ChildItem (Join-Path $base "gh-*.md") | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    $content = $content -replace "PARENT_ISSUE_URL", $parentUrl
    Set-Content $_.FullName -Value $content -NoNewline
}

Write-Host "Creating child 01 (HITL done — will close)..."
$child01Url = Publish-Child -Title "Slice 70-01 - Effect-metrics semantics spike + ADR" -BodyFile (Join-Path $base "gh-01.md") -Replacements @{}
Write-Host "Child 01: $child01Url"
Invoke-Gh issue close $child01Url --comment "HITL gate afgerond 2026-06-05. Spike: EFFECT_METRICS_SEMANTICS_SPIKE.md in slice-map."
Write-Host "Child 01 closed."

Write-Host "Creating child 02..."
$child02Url = Publish-Child -Title "Slice 70-02 - Motor CM/PM split effectbijdragen" -BodyFile (Join-Path $base "gh-02.md") -Replacements @{ "CHILD_01_ISSUE_URL" = $child01Url }
Write-Host "Child 02: $child02Url"

Write-Host "Creating child 11 (parallel met 02)..."
$child11Url = Publish-Child -Title "Slice 70-11 - Import effect-taxonomie" -BodyFile (Join-Path $base "gh-11.md") -Replacements @{ "CHILD_01_ISSUE_URL" = $child01Url }
Write-Host "Child 11: $child11Url"

Write-Host "Creating child 03..."
$child03Url = Publish-Child -Title "Slice 70-03 - Deep module EffectImpactService" -BodyFile (Join-Path $base "gh-03.md") -Replacements @{ "CHILD_02_ISSUE_URL" = $child02Url }
Write-Host "Child 03: $child03Url"

Write-Host "Creating child 04..."
$child04Url = Publish-Child -Title "Slice 70-04 - Top 10 bron Effectklasse" -BodyFile (Join-Path $base "gh-04.md") -Replacements @{ "CHILD_03_ISSUE_URL" = $child03Url }
Write-Host "Child 04: $child04Url"

Write-Host "Creating child 06..."
$child06Url = Publish-Child -Title "Slice 70-06 - FM-inspector leesbare effectresultaten" -BodyFile (Join-Path $base "gh-06.md") -Replacements @{ "CHILD_03_ISSUE_URL" = $child03Url }
Write-Host "Child 06: $child06Url"

Write-Host "Creating child 08..."
$child08Url = Publish-Child -Title "Slice 70-08 - Functierapport effect-aware scope" -BodyFile (Join-Path $base "gh-08.md") -Replacements @{ "CHILD_03_ISSUE_URL" = $child03Url }
Write-Host "Child 08: $child08Url"

Write-Host "Creating child 05..."
$child05Url = Publish-Child -Title "Slice 70-05 - Metric Effectimpact per effectcategorie" -BodyFile (Join-Path $base "gh-05.md") -Replacements @{
    "CHILD_03_ISSUE_URL" = $child03Url
    "CHILD_04_ISSUE_URL" = $child04Url
}
Write-Host "Child 05: $child05Url"

Write-Host "Creating child 09..."
$child09Url = Publish-Child -Title "Slice 70-09 - Tijdsplot per-effect jaargang" -BodyFile (Join-Path $base "gh-09.md") -Replacements @{
    "CHILD_02_ISSUE_URL" = $child02Url
    "CHILD_03_ISSUE_URL" = $child03Url
}
Write-Host "Child 09: $child09Url"

Write-Host "Creating child 10..."
$child10Url = Publish-Child -Title "Slice 70-10 - AW-pariteit EffectCost (informatief)" -BodyFile (Join-Path $base "gh-10.md") -Replacements @{
    "CHILD_01_ISSUE_URL" = $child01Url
    "CHILD_03_ISSUE_URL" = $child03Url
}
Write-Host "Child 10: $child10Url"

Write-Host "Creating child 07..."
$child07Url = Publish-Child -Title "Slice 70-07 - KPI-tabel en PBS effectkolommen" -BodyFile (Join-Path $base "gh-07.md") -Replacements @{
    "CHILD_03_ISSUE_URL" = $child03Url
    "CHILD_05_ISSUE_URL" = $child05Url
}
Write-Host "Child 07: $child07Url"

Write-Host "Creating child 12..."
$child12Url = Publish-Child -Title "Slice 70-12 - Validatie-export effecttab" -BodyFile (Join-Path $base "gh-12.md") -Replacements @{
    "CHILD_03_ISSUE_URL" = $child03Url
    "CHILD_05_ISSUE_URL" = $child05Url
    "CHILD_10_ISSUE_URL" = $child10Url
}
Write-Host "Child 12: $child12Url"

Write-Host "Creating child 13..."
$child13Url = Publish-Child -Title "Slice 70-13 - Regressie en motor-smoke in resultaten" -BodyFile (Join-Path $base "gh-13.md") -Replacements @{
    "CHILD_04_ISSUE_URL" = $child04Url
    "CHILD_05_ISSUE_URL" = $child05Url
    "CHILD_06_ISSUE_URL" = $child06Url
}
Write-Host "Child 13: $child13Url"

Write-Host ""
Write-Host "Done. Issue URLs:"
Write-Host "  Parent: $parentUrl"
Write-Host "  01:     $child01Url (closed)"
Write-Host "  02:     $child02Url  <- start here"
Write-Host "  03:     $child03Url"
Write-Host "  04:     $child04Url"
Write-Host "  05:     $child05Url"
Write-Host "  06:     $child06Url"
Write-Host "  07:     $child07Url"
Write-Host "  08:     $child08Url"
Write-Host "  09:     $child09Url"
Write-Host "  10:     $child10Url"
Write-Host "  11:     $child11Url  (parallel met 02)"
Write-Host "  12:     $child12Url"
Write-Host "  13:     $child13Url"
Write-Host ""
Write-Host "Update issues/INDEX.md and local NN.md files with GitHub URLs."
