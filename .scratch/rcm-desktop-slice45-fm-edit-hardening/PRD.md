# PRD — RCM2 desktop slice 45 (FM-bewerken hardening, quick wins)

**Status:** ready-for-agent  
**Triage:** ready-for-agent  
**Type:** AFK (adapter + kleine view-fixes)  
**Parent:** slice 44 + architectuur-review 2026-05-23  
**Datum:** 2026-05-23

## Problem Statement

Slice 44 leverde de faalwijze-editor en commit-seam. Architectuur-review vond **twee low-risk defecten/gaten** die zonder grote refactor AFK opgelost kunnen worden; overige aanbevelingen staan in `ARCHITECTURE_DEFERRED.md`.

## Solution

Twee tracer-bullet issues:

1. **Legacy Validate save-seam** — `materialize_for_save()` ontbreekt op `FaalwijzenEditService` terwijl `ValidateWindow` die aanroept.
2. **Gedeelde PBS/taakgroep-waarschuwingen** — tellers gebruiken baseline-project i.p.v. de geïsoleerde **EditingSession** in de editor.

Geen nieuwe UI-features, geen registry-uitbreiding, geen ValidateWindow-split.

## Out of scope

Zie `ARCHITECTURE_DEFERRED.md`.
