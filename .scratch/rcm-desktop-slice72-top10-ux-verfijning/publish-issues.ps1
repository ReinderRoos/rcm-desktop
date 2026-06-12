# Publish slice 72 issues to GitHub (requires: gh auth login)
# Run from repo root:
#   .\.scratch\rcm-desktop-slice72-top10-ux-verfijning\publish-issues.ps1

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
$parentUrl = New-GhIssue -Title "Slice 72 - Top 10 UX-verfijning (parent)" -BodyFile (Join-Path $base "gh-parent.md")
Write-Host "Parent: $parentUrl"

Get-ChildItem (Join-Path $base "gh-*.md") | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    $content = $content -replace "PARENT_ISSUE_URL", $parentUrl
    Set-Content $_.FullName -Value $content -NoNewline
}

Write-Host "Creating child 00..."
$child00Url = Publish-Child -Title "Slice 72-00 - NB-effectfilter dropdown opent bij klik" -BodyFile (Join-Path $base "gh-00.md") -Replacements @{}
Write-Host "Child 00: $child00Url"

Write-Host "Creating child 05 (display-seam, blocker for 03)..."
$child05Url = Publish-Child -Title "Slice 72-05 - Display-seam bijdragen-waarden" -BodyFile (Join-Path $base "gh-05.md") -Replacements @{}
Write-Host "Child 05: $child05Url"

Write-Host "Creating child 01..."
$child01Url = Publish-Child -Title "Slice 72-01 - Faalwijze standaard; Component-bron verwijderen" -BodyFile (Join-Path $base "gh-01.md") -Replacements @{}
Write-Host "Child 01: $child01Url"

Write-Host "Creating child 02..."
$child02Url = Publish-Child -Title "Slice 72-02 - Top 10 chart-only (tabel verwijderen)" -BodyFile (Join-Path $base "gh-02.md") -Replacements @{}
Write-Host "Child 02: $child02Url"

Write-Host "Creating child 03..."
$child03Url = Publish-Child -Title "Slice 72-03 - Staaflabels volgen metric en uren/%-weergave" -BodyFile (Join-Path $base "gh-03.md") -Replacements @{ "CHILD_05_ISSUE_URL" = $child05Url }
Write-Host "Child 03: $child03Url"

Write-Host "Creating child 04..."
$child04Url = Publish-Child -Title "Slice 72-04 - NB-effectfilter end-to-end op Top 10 bijdragen" -BodyFile (Join-Path $base "gh-04.md") -Replacements @{
    "CHILD_00_ISSUE_URL" = $child00Url
    "CHILD_03_ISSUE_URL" = $child03Url
}
Write-Host "Child 04: $child04Url"

Write-Host ""
Write-Host "Done. Issue URLs:"
Write-Host "  Parent: $parentUrl"
Write-Host "  00:     $child00Url  <- start here (P0)"
Write-Host "  05:     $child05Url  <- then display-seam"
Write-Host "  01:     $child01Url  (parallel)"
Write-Host "  02:     $child02Url  (parallel)"
Write-Host "  03:     $child03Url"
Write-Host "  04:     $child04Url  <- afronding"
Write-Host ""
Write-Host "Update issues/INDEX.md and local NN.md files with GitHub URLs."
