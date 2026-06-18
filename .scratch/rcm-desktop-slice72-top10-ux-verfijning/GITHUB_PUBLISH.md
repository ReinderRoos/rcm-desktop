# GitHub publicatie — Slice 72

## Vereisten

```powershell
gh auth login
```

## Publiceren

Vanaf repo-root:

```powershell
.\.scratch\rcm-desktop-slice72-top10-ux-verfijning\publish-issues.ps1
```

Het script:

1. Maakt parent issue + 6 child issues aan met label `ready-for-agent`
2. Vult `PARENT_ISSUE_URL` en `CHILD_*_ISSUE_URL` placeholders in `gh-*.md`
3. Print alle URLs

## Na publicatie

- Update `issues/INDEX.md` GitHub-kolom
- Optioneel: koppel parent aan project board

## Implementatie starten

```
/tdd slice 72 issue 00
```
