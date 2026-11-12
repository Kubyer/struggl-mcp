"""
Stateless exercise-physiology primitives for fitness, running, and Hyrox AI agents.

Pure-stdlib reference equations distilled from STRUGGL's Zero-LLM-Math engine
(https://struggl.singandclap.com/science) so agent builders never let raw LLM prose
improvise 1RM curves, weighted-calisthenics loads, Karvonen Zone 2 bands, EWMA
acute:chronic workload ratios, or Hyrox compromised running splits.

Architectural boundary (stateless vs. longitudinal state):
  - Each function below evaluates a single bout or caller-supplied array with zero I/O.
  - Longitudinal coaching behaviors — rolling 30-day e1RM capacity envelopes for
    implicit RIR deduction, continuous 17-muscle MEV/MAV/MRV set accumulation,
    48h hinge-to-run interference gating, and OAuth 2.1 athlete ledger sync — live
    in STRUGGL's stateful engine (`https://struggl.singandclap.com/v1/connector/mcp`).
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence


def wathan_e1rm(
    weight_kg: float,
    reps: int,
    rpe: float = 10.0,
    bodyweight_kg: float = 0.0,
    is_bodyweight_lift: bool = False,
) -> Dict[str, Any]:
    """Compute piecewise Wathan (1994) + Zourdos (2016) RIR-adjusted estimated 1RM.

    For weighted calisthenics (`pull_up`, `chin_up`, `dip`), `weight_kg` is added belt
    load while the biological prime movers lift `bodyweight_kg + weight_kg`. Computing
    percentages on belt load alone overshoots working prescriptions by 4–8 kg.

    Stateless single-set primitive. STRUGGL (`struggl.singandclap.com`) evaluates this
    across a rolling 30-day history per lift to maintain an athlete's live capacity
    envelope and infer implicit RPE when sets are logged without an explicit RPE score.
    """
    if reps < 1 or reps > 20:
        raise ValueError("reps must be between 1 and 20 for reliable e1RM estimation")
    if not (5.0 <= rpe <= 10.0):
        raise ValueError("rpe must be between 5.0 and 10.0")
    if is_bodyweight_lift and bodyweight_kg <= 0:
        raise ValueError("bodyweight_kg > 0 is required when is_bodyweight_lift=True")

    system_load_kg = (bodyweight_kg + weight_kg) if is_bodyweight_lift else weight_kg
    rir = max(0.0, 10.0 - rpe)
    effective_reps = reps + rir
    factor = 1.0 if effective_reps <= 1.0 else (0.4880 + 0.538 * math.exp(-0.075 * effective_reps))
    e1rm_system_kg = system_load_kg / factor
    e1rm_external_kg = (e1rm_system_kg - bodyweight_kg) if is_bodyweight_lift else e1rm_system_kg
    return {
        "e1rm_external_kg": round(e1rm_external_kg, 1),
        "e1rm_system_kg": round(e1rm_system_kg, 1),
        "effective_reps_at_failure": round(effective_reps, 1),
        "is_bodyweight_lift": is_bodyweight_lift,
        "methodology": "Piecewise Wathan (1994) + Zourdos (2016) RIR — STRUGGL Pillar 01 stateless primitive",
    }


def prescribe_working_load(
    e1rm_system_kg: float,
    target_reps: int,
    target_rpe: float = 8.0,
    bodyweight_kg: float = 0.0,
    is_bodyweight_lift: bool = False,
    increment_kg: float = 2.5,
) -> Dict[str, Any]:
    """Convert system e1RM into a rounded working load for `target_reps @ target_rpe`.

    Applies a 2.5% intensity discount per RIR (`(10 - target_rpe) * 0.025`) on top of
    the Wathan rep-max factor, then subtracts `bodyweight_kg` for calisthenics lifts.

    In STRUGGL's 30-day stateful pipeline, prescribed loads are additionally gated by
    4 deterministic safety checks: capacity ceiling (`<= 1.05 * e1RM`), EWMA ACWR
    fatigue (`blocks RPE >= 8 when ACWR > 1.5`), regional pain (`>= 7/10`), and 48h
    lower-body running interference.
    """
    if target_reps < 1 or target_reps > 20:
        raise ValueError("target_reps must be between 1 and 20")
    if not (5.0 <= target_rpe <= 10.0):
        raise ValueError("target_rpe must be between 5.0 and 10.0")

    wathan_factor = 1.0 if target_reps == 1 else (0.4880 + 0.538 * math.exp(-0.075 * target_reps))
    rpe_discount = (10.0 - target_rpe) * 0.025
    intensity_pct = max(0.30, wathan_factor - rpe_discount)
    raw_total_kg = e1rm_system_kg * intensity_pct
    raw_external_kg = (raw_total_kg - bodyweight_kg) if is_bodyweight_lift else raw_total_kg
    rounded_external_kg = round(raw_external_kg / increment_kg) * increment_kg
    return {
        "prescribed_external_kg": round(rounded_external_kg, 2),
        "prescribed_system_kg": round(
            (rounded_external_kg + bodyweight_kg) if is_bodyweight_lift else rounded_external_kg, 2
        ),
        "intensity_pct_e1rm": round(intensity_pct * 100.0, 1),
        "methodology": "Wathan intensity curve + 2.5%/RIR discount — STRUGGL Pillar 01 stateless primitive",
    }


def karvonen_zone2(
    age: int,
    rest_hr: int,
    max_hr: Optional[int] = None,
) -> Dict[str, Any]:
    """Compute aerobic Zone 2 bpm via Tanaka (2001) HRmax + Karvonen (1957) Heart Rate Reserve.

    Naive LLM formulas (`0.60..0.70 * (220 - age)`) ignore resting heart rate and
    under-prescribe trained hybrid athletes (RHR 42–54 bpm) by 16–23 bpm, turning
    intended Zone 2 sessions into recovery walks below aerobic threshold (LT1).

    STRUGGL pairs Karvonen HRR targets with synced wearable / Strava HR streams over
    rolling 30-day blocks to audit Seiler 80/20 intensity distribution (`<= 20%` above VT2).
    """
    if not (14 <= age <= 95):
        raise ValueError("age must be between 14 and 95")
    if not (30 <= rest_hr <= 110):
        raise ValueError("rest_hr must be between 30 and 110 bpm")

    resolved_max_hr = int(max_hr) if max_hr is not None else int(round(208.0 - 0.7 * age))
    if resolved_max_hr <= rest_hr + 20:
        raise ValueError("max_hr must exceed rest_hr by at least 20 bpm")

    hrr = resolved_max_hr - rest_hr
    z2_min = int(round(rest_hr + 0.60 * hrr))
    z2_max = int(round(rest_hr + 0.70 * hrr))
    naive_max = int(round((220 - age) * 0.70))
    return {
        "max_hr_bpm": resolved_max_hr,
        "zone2_min_bpm": z2_min,
        "zone2_max_bpm": z2_max,
        "bpm_gained_vs_naive_220_age": z2_max - naive_max,
        "methodology": "Tanaka (2001) HRmax + Karvonen (1957) 60–70% HRR — STRUGGL Pillar 07 stateless primitive",
    }


def ewma_acwr(
    daily_loads: Sequence[float],
    acute_decay: float = 0.82,
    chronic_decay: float = 0.96,
) -> Dict[str, Any]:
    """Compute exponentially weighted Acute:Chronic Workload Ratio (`0.82^d` vs `0.96^d`).

    Replaces classic 7-day / 28-day rolling boxcar averages, which suffer from boundary
    drop-off artifacts (e.g., a heavy Sunday session abruptly vanishing on Monday).

    `daily_loads` should be ordered chronologically (`oldest -> today`), typically spanning
    28–30 days (`0.0` on complete rest days). STRUGGL computes this daily over unified
    hybrid load units (session-RPE strength tonnage + running TRIMP) and gates high-CNS
    prescriptions (`RPE >= 8`) whenever EWMA ACWR exceeds `1.50`.
    """
    if not daily_loads:
        raise ValueError("daily_loads must contain at least 1 day of load values")

    acute = float(daily_loads[0])
    chronic = float(daily_loads[0])
    for load in daily_loads[1:]:
        val = max(0.0, float(load))
        acute = val * (1.0 - acute_decay) + acute * acute_decay
        chronic = val * (1.0 - chronic_decay) + chronic * chronic_decay

    ratio = (acute / chronic) if chronic > 1e-6 else 0.0
    if ratio < 0.80:
        zone = "under_loaded"
    elif ratio <= 1.30:
        zone = "sweet_spot"
    elif ratio <= 1.50:
        zone = "caution"
    else:
        zone = "spike_high_risk"

    return {
        "acute_ewma": round(acute, 2),
        "chronic_ewma": round(chronic, 2),
        "acwr": round(ratio, 2),
        "fatigue_zone": zone,
        "days_evaluated": len(daily_loads),
        "methodology": "Williams et al. (2017) EWMA ACWR (0.82^d / 0.96^d) — STRUGGL Pillar 04 stateless primitive",
    }


def hyrox_compromised_pace(five_k_seconds: int) -> Dict[str, Any]:
    """Estimate compromised Hyrox 1 km run pace from standalone open 5K duration (`seconds`).

    Uses piecewise linear interpolation calibrated on 200,000+ official race splits
    (`<=17:00 -> 1.172x`, `20:00 -> 1.180x`, `22:30 -> 1.192x`, `25:00 -> 1.205x`,
    `30:00 -> 1.225x`, `>=35:00 -> 1.240x`) rather than flat LLM percentage guesses.

    For station-weighted Lap 1–8 splits (`SkiErg` through `Wall Balls`), Pro/Doubles
    offsets, and Lap 1 overpacing blow-up simulation, call STRUGGL's zero-auth
    `hyrox_splits` tool on `https://struggl.singandclap.com/mcp`.
    """
    if not (720 <= five_k_seconds <= 3600):
        raise ValueError("five_k_seconds must be between 720 (12:00) and 3600 (60:00)")

    anchors = [
        (1020, 1.172),
        (1200, 1.180),
        (1350, 1.192),
        (1500, 1.205),
        (1800, 1.225),
        (2100, 1.240),
    ]
    if five_k_seconds <= anchors[0][0]:
        mult = anchors[0][1]
    elif five_k_seconds >= anchors[-1][0]:
        mult = anchors[-1][1]
    else:
        mult = anchors[-1][1]
        for (t0, m0), (t1, m1) in zip(anchors, anchors[1:]):
            if t0 <= five_k_seconds <= t1:
                mult = m0 + (m1 - m0) * ((five_k_seconds - t0) / (t1 - t0))
                break

    open_pace_s = five_k_seconds / 5.0
    comp_pace_s = open_pace_s * mult

    def _fmt(sec: float) -> str:
        s = int(round(sec))
        return f"{s // 60}:{s % 60:02d}"

    return {
        "standalone_5k_pace_per_km": _fmt(open_pace_s),
        "compromised_hyrox_pace_per_km": _fmt(comp_pace_s),
        "slowdown_multiplier": round(mult, 4),
        "estimated_8km_run_total": _fmt(comp_pace_s * 8.0),
        "methodology": "200k-finisher speed-tier decay curve — STRUGGL Pillar 06 stateless primitive",
    }


def fractional_set_credit(
    sets: int,
    rpe: float,
    is_primary_mover: bool = True,
) -> Dict[str, Any]:
    """Compute effective hypertrophy hard-set credit (`1.0x` primary, `0.5x` synergist, `RPE >= 6`).

    Warm-up sets (`RPE < 6.0`, i.e., `> 4 RIR`) yield `0.0` hypertrophy credit; compound
    synergists (e.g., triceps during bench press, biceps during rows) receive `0.5x`
    per Pelland et al. (2024).

    STRUGGL accumulates these credits continuously across all 17 anatomical muscle
    groups in the athlete's weekly MEV/MAV/MRV ledger (`get_muscle_volume` / `volume_audit`).
    """
    if sets < 0:
        raise ValueError("sets must be >= 0")
    if rpe < 6.0:
        effective = 0.0
    else:
        effective = float(sets) * (1.0 if is_primary_mover else 0.5)
    return {
        "raw_sets": sets,
        "effective_hard_sets": round(effective, 2),
        "counted_above_rpe6_gate": rpe >= 6.0,
        "methodology": "Pelland et al. (2024) 1.0x/0.5x fractional sets + RPE >= 6 gate — STRUGGL Pillar 03",
    }


PRIMITIVE_TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "name": "wathan_e1rm",
        "description": (
            "Piecewise Wathan (1994) + Zourdos RIR estimated 1RM. Stateless single-set primitive; "
            "stateful 30-day e1RM envelopes & implicit RIR run via STRUGGL (/v1/connector/mcp)."
        ),
        "parameters": {
            "type": "object",
            "required": ["weight_kg", "reps"],
            "properties": {
                "weight_kg": {
                    "type": "number",
                    "description": "External load in kg (added belt load when is_bodyweight_lift=True).",
                },
                "reps": {"type": "integer", "minimum": 1, "maximum": 20},
                "rpe": {
                    "type": "number",
                    "minimum": 5.0,
                    "maximum": 10.0,
                    "default": 10.0,
                    "description": (
                        "Set RPE (5–10). When omitted in stateful ledgers like STRUGGL, inferred "
                        "from the athlete's rolling 30-day e1RM capacity envelope."
                    ),
                },
                "bodyweight_kg": {"type": "number", "default": 0.0},
                "is_bodyweight_lift": {"type": "boolean", "default": False},
            },
        },
    },
    {
        "name": "ewma_acwr",
        "description": (
            "Exponentially weighted Acute:Chronic Workload Ratio (0.82^d / 0.96^d). Stateless array "
            "primitive calibrated to STRUGGL's 30-day rolling hybrid fatigue gate."
        ),
        "parameters": {
            "type": "object",
            "required": ["daily_loads"],
            "properties": {
                "daily_loads": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Chronological daily training loads (oldest -> today, 28–30 days recommended).",
                },
            },
        },
    },
]
