# ICG v0.4 — Integrated Stable Snapshot

**Tag:** `ICG_v0.4_Integrated_Stable`
**Created:** 2026-08-27 18:55
**Archive:** `ICG_v0.4_Integrated_Stable_20260827_1855.zip`

This marks the point where the ICG v0.4 module was integrated into the live UniPlag
pipeline (Aris Directive, report 16) and **approved for production** (Aris verdict, report 17).

## Contents of the snapshot
- `app/icg/` — full ICG v0.4 module (graph_builder, nli_verifier, synthesis_verifier,
  external_search, red_team, blind_benchmark, integration, icg_watchdog, models, etc.)
  plus the sealed reference matrices in `app/icg/benchmarks/reference/`.
- `app/checker.py` — `run_check()` now calls `check_icg_fast()` (Fast contour, default),
  adds degradation disclaimer, and schedules the background watchdog.
- `app/db.py` — new `ICGHealth` model (`icg_health` table).
- `app/main.py` — admin control interface `/admin/icg` + watchdog/deep trigger routes.

## Fixed watchdog baselines (constant, not floating)
The watchdog compares against the sealed reference, NOT live recomputed floats:
- Blind (Fast): 19/22
- RedTeam (Fast): 17/30
Source of truth: `app/icg/benchmarks/reference/icg_stability_map_v04.json`.

## Health segregation (Aris Directive)
- User report: shows the ICG "Интеллектуальный вклад" section; **never** reveals
  degradation/HealthRecord.
- Admin-only: `/admin/icg` shows HealthRecord history + degradation status.
- On degradation (`degraded > 0`), new checks get `degraded=True` + a general
  accuracy disclaimer inside `icg_json` (internal tracing only).

## Watchdog logging (Aris Directive)
- Watchdog startup and OK completion: `INFO`.
- Degradation (`degraded > 0`): `WARNING`, names the failed benchmark (Red or Blind).
