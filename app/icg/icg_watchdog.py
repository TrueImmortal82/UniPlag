"""
ICG Watchdog (app/icg/icg_watchdog.py)
=======================================
Aris Directive: autonomous health mechanism.
- Runs red_team_benchmark_30 + blind_benchmark (FAST contour) and compares to sealed v0.4 baselines.
- Writes an ICGHealth row (black-box history).
- Thresholds: RedTeam < 17/30 -> Warning(1); Blind < 19/22 -> Critical(2).
- On degradation the system must add a disclaimer to new checks.
Frequency: every 6 hours OR after every 500 checks (whichever first).
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import json
import logging

from .red_team import run_red_team_benchmark_30
from .blind_benchmark import run_blind_benchmark
from .external_reality_benchmark import run_external_reality_benchmark
from .empirical_assault_v2 import run_empirical_assault_fast

# Aris Directive: server logging for the watchdog & degradation signal.
logger = logging.getLogger("icg.watchdog")

# Sealed v0.4 Fast baselines (single source of truth).
REFERENCE_DIR = Path(__file__).resolve().parent / "benchmarks" / "reference"
FAST_BLIND_OK = 19
FAST_BLIND_TOT = 22
FAST_RED_OK = 17
FAST_RED_TOT = 30
WARN_RED_BELOW = FAST_RED_OK      # RedTeam < 17/30 -> Warning
CRIT_BLIND_BELOW = FAST_BLIND_OK  # Blind < 19/22 -> Critical

WATCHDOG_INTERVAL_HOURS = 6
WATCHDOG_CHECK_INTERVAL = 500

DEGRADED_DISCLAIMER = "Р’РЅРёРјР°РЅРёРµ: С‚РѕС‡РЅРѕСЃС‚СЊ ICG РІСЂРµРјРµРЅРЅРѕ СЃРЅРёР¶РµРЅР° (СЂРµРіСЂРµСЃСЃРёСЏ v0.4)."
DEGRADED_LEVELS = {0: "ok", 1: "warning", 2: "critical"}


def _load_baselines() -> Dict[str, Any]:
    bs = {"fast_blind_ok": FAST_BLIND_OK, "fast_blind_tot": FAST_BLIND_TOT,
          "fast_red_ok": FAST_RED_OK, "fast_red_tot": FAST_RED_TOT}
    try:
        ref = REFERENCE_DIR / "icg_stability_map_v04.json"
        if ref.exists():
            data = json.loads(ref.read_text(encoding="utf-8"))
            agg = data.get("aggregate_fast", {})
            bs["fast_blind_ok"] = int(agg.get("blind", FAST_BLIND_OK))
            bs["fast_blind_tot"] = int(agg.get("blind_tot", FAST_BLIND_TOT))
            bs["fast_red_ok"] = int(agg.get("red", FAST_RED_OK))
            bs["fast_red_tot"] = int(agg.get("red_tot", FAST_RED_TOT))
    except Exception:
        pass
    return bs


def _run_dead_zones() -> Dict[str, Any]:
    """Inventory of the formerly-dead 'dead-zone' benchmarks (Aris Directive #2).

    Executes the External Reality Benchmark and the Empirical Assault v2 suite on
    the FAST (no-LLM) contour and transparently records their pass state. These
    were previously only reachable via `__main__` (hence 'dead zones') — now they
    are part of the periodic health run.
    """
    # External Reality Benchmark may not tolerate stdout suppression broadly; keep
    # verbose off so it stays quiet for the health record.
    try:
        ext = run_external_reality_benchmark(verbose=False)
        ext_ok = {
            "p1_accuracy": float(ext.get("p1_accuracy", 0.0)),
            "dsa": float(ext.get("dsa", 0.0)),
            "gir": float(ext.get("gir", 0.0)),
            "macro_f1": float(ext.get("macro_f1", 0.0)),
        }
        ext_pass = ext_ok["p1_accuracy"] >= 0.8 and ext_ok["dsa"] >= 80.0 and ext_ok["gir"] >= 80.0
    except Exception as e:  # never crash the health check
        ext_ok = {"error": str(e)}
        ext_pass = False

    try:
        assault = run_empirical_assault_fast(verbose=False)
        assault_pass = assault["passed"] >= 3  # >=3/4 cognitive-immunity cases must hold
        assault_digest = {
            "passed": assault.get("passed", 0),
            "total": assault.get("total", 4),
            "pass_rate": assault.get("pass_rate", 0.0),
            "cases": assault.get("cases", {}),
        }
    except Exception as e:
        assault_digest = {"error": str(e)}
        assault_pass = False

    return {
        "external_reality": {"pass": ext_pass, **ext_ok},
        "empirical_assault_v2": {"pass": assault_pass, **assault_digest},
        "dead_zones_pass": ext_pass and assault_pass,
    }


def run_watchdog_once(session) -> Dict[str, Any]:
    """Run both benchmarks on the FAST contour and persist an ICGHealth row."""
    bs = _load_baselines()

    # Aris Directive: INFO-level log at watchdog start.
    logger.info("ICG watchdog run started (Fast contour, baselines: blind %s/%s red %s/%s)",
                bs["fast_blind_ok"], bs["fast_blind_tot"], bs["fast_red_ok"], bs["fast_red_tot"])

    red = run_red_team_benchmark_30(verbose=False)
    blind = run_blind_benchmark(verbose=False)
    dead_zones = _run_dead_zones()

    red_score = int(red.get("passed", 0))
    blind_score = int(blind.get("total_passed", 0))

    # Levels: 0 ok, 1 warning (red below), 2 critical (blind below)
    level = 0
    reasons = []
    if blind_score < bs["fast_blind_ok"]:
        level = 2
        reasons.append(f"blind {blind_score}/{bs['fast_blind_tot']} < baseline {bs['fast_blind_ok']}/{bs['fast_blind_tot']}")
    elif red_score < bs["fast_red_ok"]:
        level = 1
        reasons.append(f"red_team {red_score}/{bs['fast_red_tot']} < baseline {bs['fast_red_ok']}/{bs['fast_red_tot']}")
    # Aris Directive #2: dead-zone benchmarks feed the degradation signal.
    if not dead_zones["dead_zones_pass"] and level == 0:
        level = 1
        reasons.append("dead-zone benchmarks degraded (external_reality / empirical_assault)")

    details = {
        "baselines": bs,
        "red_team": {"score": red_score, "total": bs["fast_red_tot"],
                     "pass_rate": red.get("pass_rate")},
        "blind": {"score": blind_score, "total": bs["fast_blind_tot"],
                  "accuracy": blind.get("accuracy"), "macro_f1": blind.get("macro_f1")},
        "dead_zones": dead_zones,
        "level": DEGRADED_LEVELS[level],
        "reasons": reasons,
    }

    try:
        from ..db import ICGHealth
        rec = ICGHealth(
            blind_score=blind_score,
            blind_tot=bs["fast_blind_tot"],
            red_score=red_score,
            red_tot=bs["fast_red_tot"],
            degraded=level,
            details_json=json.dumps(details, ensure_ascii=False),
            triggered_by="periodic",
        )
        session.add(rec)
        session.commit()
    except Exception as e:  # non-fatal: health history must never crash the check
        details["persist_error"] = str(e)

    # Aris Directive: degradation must log at WARNING and name the failed benchmark.
    if level > 0:
        logger.warning("ICG degradation detected (level=%d): %s",
                       level, "; ".join(reasons) if reasons else "unspecified")
    else:
        logger.info("ICG watchdog run completed OK (blind %s/%s, red %s/%s)",
                    blind_score, bs["fast_blind_tot"], red_score, bs["fast_red_tot"])

    return {"level": level, "degraded": level > 0, "details": details}


def last_health(session) -> Optional[Any]:
    try:
        from ..db import ICGHealth
        return session.query(ICGHealth).order_by(ICGHealth.id.desc()).first()
    except Exception:
        return None


def current_degraded(session) -> bool:
    """Is the system currently considered degraded (last health record says so)?"""
    h = last_health(session)
    if h is None:
        return False
    return int(h.degraded) > 0


def should_run_watchdog(session, check_count_since_last: int) -> bool:
    h = last_health(session)
    if h is None:
        return True
    # every 6h
    if h.ts is None or (datetime.utcnow() - h.ts) >= timedelta(hours=WATCHDOG_INTERVAL_HOURS):
        return True
    # after every 500 checks
    if check_count_since_last >= WATCHDOG_CHECK_INTERVAL:
        return True
    return False

