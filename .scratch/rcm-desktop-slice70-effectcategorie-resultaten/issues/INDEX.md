# Slice 70 — issues



**PRD:** [PRD.md](../PRD.md)  

**Status:** **goedgekeurd** — GitHub publicatie pending ([GITHUB_PUBLISH.md](../GITHUB_PUBLISH.md))



| # | Title | Type | Triage | Blocked by | GitHub |

|---|--------|------|--------|------------|--------|

| [01](01.md) | Effect-metrics semantics spike + ADR | HITL | **done** | slice 69 | *(publish + close)* |

| [02](02.md) | Motor: CM/PM split effectbijdragen | AFK | ready-for-agent | 01 | TBD |

| [03](03.md) | Deep module EffectImpactService | AFK | ready-for-agent | 02 | TBD |

| [04](04.md) | Top 10 bron Effectklasse | AFK | ready-for-agent | 03 | TBD |

| [05](05.md) | Metric Effectimpact per effectcategorie | AFK | ready-for-agent | 03, 04 | TBD |

| [06](06.md) | FM-inspector leesbare effectresultaten | AFK | ready-for-agent | 03 | TBD |

| [07](07.md) | KPI-tabel & PBS effectkolommen | AFK | ready-for-agent | 03, 05 | TBD |

| [08](08.md) | Functierapport effect-aware scope | AFK | ready-for-agent | 03 | TBD |

| [09](09.md) | Tijdsplot per-effect jaargang | AFK | ready-for-agent | 02, 03 | TBD |

| [10](10.md) | AW-pariteit EffectCost (informatief) | AFK | ready-for-agent | 01, 03 | TBD |

| [11](11.md) | Import effect-taxonomie | AFK | ready-for-agent | 01 | TBD |

| [12](12.md) | Validatie-export effecttab | AFK | ready-for-agent | 03, 05, 10 | TBD |

| [13](13.md) | Regressie & motor-smoke in resultaten | AFK | ready-for-agent | 04–06 | TBD |



## Implementatievolgorde



1. ~~**01** (HITL)~~ — **done** [`EFFECT_METRICS_SEMANTICS_SPIKE.md`](../EFFECT_METRICS_SEMANTICS_SPIKE.md)

2. **02** → **03** (motor split + `EffectImpactService`); **11** parallel met 02

3. **04**, **05**, **06**, **08** parallel na 03

4. **07**, **09** na 05 resp. 02+03

5. **10**, **12** na 03+05

6. **13** afronding + KANBAN_HANDOFF



## GitHub publiceren



```powershell

gh auth login

.\.scratch\rcm-desktop-slice70-effectcategorie-resultaten\publish-issues.ps1

```



Issue bodies: `issues/gh-parent.md`, `issues/gh-01.md` … `issues/gh-13.md`



## Start



```

/tdd slice 70 issue 02

```


