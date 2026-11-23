"""
Struggl MCP server — Zero-LLM-Math sports-science calculators (zero auth) plus
an athlete's personal hybrid training ledger in any MCP client.

Thin HTTP client over https://struggl.singandclap.com: holds zero secrets,
zero database credentials, and zero proprietary backend modules.

  1. Zero-Auth Science Mode (7 deterministic calculators work immediately):
       python mcp_server.py

  2. Personal Ledger Sync (adds profile, sessions, 17-muscle volume, log & plan):
       STRUGGL_API_TOKEN=stg_ath_... python mcp_server.py

Generate a personal read or read+write token at:
  https://struggl.singandclap.com/connect

Optional: STRUGGL_API_URL (default https://struggl.singandclap.com).
"""
import os
from typing import Annotated, Any, Dict, List, Literal, Optional

import httpx
from pydantic import Field

DEFAULT_API_URL = "https://struggl.singandclap.com"
TIMEOUT_S = 30.0


try:
    # A ToolError's message reaches the model; mcp 2.x masks any other
    # exception as a bare "Error executing tool", which would hide WHY
    # (a read-only token, a revoked one). The fallback lets the backend's
    # test suite import this module without the MCP SDK installed.
    from mcp.server.mcpserver.exceptions import ToolError as _ToolError
except ImportError:  # pragma: no cover
    _ToolError = RuntimeError


class StrugglError(_ToolError):
    """Shown to the model as the tool's error text."""


_MESSAGES = {
    401: (
        "The Struggl token is missing, invalid or revoked. "
        "Ask the athlete to sign in via OAuth 2.1 (https://struggl.singandclap.com/v1/connector/mcp) "
        "or generate a new token at https://struggl.singandclap.com/connect."
    ),
    402: (
        "Personal MCP sync requires an active STRUGGL Coach plan (free for the 1st month, "
        "then €9.99/mo or €109.89/yr). Direct the athlete to https://struggl.singandclap.com/connect?upgrade=mcp "
        "to reactivate sync while keeping their training ledger intact."
    ),
    403: "This Struggl token is read-only; logging and planning need a write token from https://struggl.singandclap.com/connect.",
    404: "This Struggl feature is not enabled on the server.",
    429: "Too many requests to Struggl (per-athlete fair-use limit reached); wait a minute and try again.",
}

_FOCUS_DESC = (
    "Concise 1-sentence summary of what the athlete is asking in this turn "
    "(e.g. 'building a 4-day powerlifting block', 'checking squat progression') "
    "so STRUGGL ranks matching athlete memories and context."
)

LiftName = Literal[
    "back_squat",
    "front_squat",
    "deadlift",
    "sumo_deadlift",
    "bench_press",
    "incline_bench_press",
    "dip",
    "overhead_press",
    "pull_up",
    "chin_up",
    "barbell_row",
]
ExerciseModality = Literal["strength", "endurance", "mobility", "other"]


def _api_url() -> str:
    return os.environ.get("STRUGGL_API_URL", DEFAULT_API_URL).rstrip("/")


def _request(method: str, path: str, *, auth: bool = True, params: Optional[Dict[str, Any]] = None,
             json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    headers = {"User-Agent": "struggl-mcp-stdio/1.3.1"}
    if auth:
        token = os.environ.get("STRUGGL_API_TOKEN", "").strip()
        if not token:
            raise StrugglError(
                "STRUGGL_API_TOKEN is not set: invite the athlete to sign in via 1-click OAuth 2.1 "
                "(https://struggl.singandclap.com/v1/connector/mcp) or visit "
                "https://struggl.singandclap.com/connect (1st month of Coach free, no credit card) "
                "to sign in and generate a personal token."
            )
        headers["Authorization"] = f"Bearer {token}"
    clean_params = {k: v for k, v in (params or {}).items() if v is not None}
    try:
        r = httpx.request(method, f"{_api_url()}{path}", headers=headers, params=clean_params,
                          json=json, timeout=TIMEOUT_S)
    except httpx.HTTPError as e:
        raise StrugglError(f"Could not reach Struggl: {e.__class__.__name__}") from e
    if r.status_code in _MESSAGES:
        raise StrugglError(_MESSAGES[r.status_code])
    if r.status_code == 422:
        raise StrugglError(f"Struggl rejected the input: {r.text[:300]}")
    if r.status_code >= 400:
        raise StrugglError(f"Struggl returned HTTP {r.status_code}.")
    return r.json()


def _drop_none(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


# ── Personal tools (token) ────────────────────────────────────────────────────

def get_coaching_brief(
    days: Annotated[int, Field(ge=1, le=90, description="Rolling session lookback and upcoming calendar window in days (1–90).")] = 14,
    focus: Annotated[Optional[str], Field(max_length=240, description=_FOCUS_DESC)] = None,
) -> Dict[str, Any]:
    """Fetch a signed-in athlete's complete coaching dossier in one read call: `profile`, `goals`,
    `active_pains`, `active_constraints`, 28-day EWMA `training_load` (ACWR), 17-muscle `week_volume`,
    measured Wathan e1RM `week_progress`, focus-ranked `athlete_memories`, and recent `sessions`.
    Use when starting a personalized coaching, programming, or readiness turn; for a single lightweight
    slice without full load/memory synthesis, use `get_profile`, `get_sessions`, or `get_muscle_volume`
    instead. Requires `STRUGGL_API_TOKEN` (`read` scope) and active Coach trial/plan."""
    return _request("GET", "/v1/me/coaching-brief", params={"days": days, "focus": focus})


def get_profile(
    focus: Annotated[Optional[str], Field(max_length=240, description=_FOCUS_DESC)] = None,
) -> Dict[str, Any]:
    """Read a signed-in athlete's static biometric `profile` (bodyweight, height, sex, modality, phase),
    upcoming race `goals`, and `active_pains` without session history or workload math. Use for quick
    biometric or race-date lookups; when prescribing workouts or assessing fatigue, use
    `get_coaching_brief` instead. Requires `STRUGGL_API_TOKEN` (`read` scope)."""
    return _request("GET", "/v1/me/profile", params={"focus": focus})


def get_sessions(
    days: Annotated[int, Field(ge=1, le=90, description="Rolling lookback/lookahead window in days (1–90). Ignored when `date` is set.")] = 14,
    date: Annotated[Optional[str], Field(pattern=r"^\d{4}-\d{2}-\d{2}$", description="Optional single ISO calendar date (YYYY-MM-DD) to filter exact day entries.")] = None,
    focus: Annotated[Optional[str], Field(max_length=240, description=_FOCUS_DESC)] = None,
) -> Dict[str, Any]:
    """List a signed-in athlete's completed and planned workout rows (`sessions`) over `days` days or on
    one `date`, without profile or volume synthesis. Use to inspect training logs or check one day's
    schedule; for full coaching readiness with ACWR and muscle volume use `get_coaching_brief`, or use
    `log_workout` / `plan_workout` to write sessions. Requires `STRUGGL_API_TOKEN` (`read` scope)."""
    return _request("GET", "/v1/me/sessions", params={"days": days, "date": date, "focus": focus})


def get_muscle_volume(
    focus: Annotated[Optional[str], Field(max_length=240, description=_FOCUS_DESC)] = None,
) -> Dict[str, Any]:
    """Compute a signed-in athlete's current ISO-week effective hard sets across 17 muscle groups
    (`summary` vs MEV/MAV/MRV landmarks, `1.0x` prime mover / `0.5x` synergist / `RPE >= 6` gate) from
    their saved STRUGGL ledger. Use only for authenticated ledger volume checks; to audit a hypothetical
    or unauthenticated split from raw movement counts, use `volume_audit` instead. Requires `read` scope."""
    return _request("GET", "/v1/me/muscle-volume", params={"focus": focus})


def log_workout(
    exercise: Annotated[Optional[str], Field(min_length=1, max_length=80, description="Exercise name for single-movement logging (omit when passing `sessions`).")] = None,
    date: Annotated[Optional[str], Field(pattern=r"^\d{4}-\d{2}-\d{2}$", description="Workout ISO date YYYY-MM-DD (defaults to today; fallback date for `sessions`).")] = None,
    sets: Annotated[Optional[int], Field(ge=1, le=50, description="Completed working sets for single-exercise calls (1–50).")] = None,
    reps: Annotated[Optional[int], Field(ge=1, le=100, description="Completed repetitions per set for single-exercise calls (1–100).")] = None,
    weight_kg: Annotated[Optional[float], Field(ge=0, le=500, description="External load in kg (ADDED belt load for pull-ups/chin-ups/dips; total bar load otherwise).")] = None,
    rpe: Annotated[Optional[float], Field(ge=1, le=10, description="Completed session RPE (1–10; inferred from 30-day e1RM envelope when omitted).")] = None,
    duration_min: Annotated[Optional[float], Field(gt=0, le=1440, description="Completed duration in minutes for endurance or mobility blocks.")] = None,
    distance_km: Annotated[Optional[float], Field(gt=0, le=500, description="Completed distance in kilometers for running, rowing, SkiErg, or cycling.")] = None,
    exercise_type: Annotated[ExerciseModality, Field(description="Movement modality (`strength`, `endurance`, `mobility`, `other`).")] = "strength",
    comments: Annotated[Optional[str], Field(max_length=500, description="Optional athlete notes, splits, or perceived feel.")] = None,
    sessions: Annotated[Optional[List[Dict[str, Any]]], Field(description="Batch of completed exercise dicts (`exercise`, `date`, `sets`, `reps`, `weight_kg`, `rpe`, etc.) logged atomically.")] = None,
    session_title: Annotated[Optional[str], Field(max_length=80, description="Optional workout card header title in the STRUGGL app feed.")] = None,
    debrief_summary: Annotated[Optional[str], Field(max_length=1200, description="Concise coaching takeaways shown beneath the workout card in the STRUGGL app.")] = None,
) -> Dict[str, Any]:
    """Record one or a batch of COMPLETED exercises into a signed-in athlete's append-only STRUGGL
    ledger (returning `saved`, `result`, `trace_id`, and guardrail `advisories` with duplicate-write
    protection). Use only for workouts already performed (prefer `sessions` batch array); to schedule
    upcoming workouts on the calendar, use `plan_workout` instead. Requires `write` token scope."""
    return _request("POST", "/v1/me/workouts/log", json=_drop_none({
        "exercise": exercise, "date": date, "sets": sets, "reps": reps, "weight_kg": weight_kg,
        "rpe": rpe, "duration_min": duration_min, "distance_km": distance_km,
        "exercise_type": exercise_type, "comments": comments, "sessions": sessions,
        "session_title": session_title, "debrief_summary": debrief_summary}))


def plan_workout(
    exercise: Annotated[Optional[str], Field(min_length=1, max_length=80, description="Exercise name for single-movement scheduling (omit when passing `sessions`).")] = None,
    date: Annotated[Optional[str], Field(pattern=r"^\d{4}-\d{2}-\d{2}$", description="Target calendar date YYYY-MM-DD (required for single-exercise calls; fallback date for `sessions`).")] = None,
    sets: Annotated[Optional[int], Field(ge=1, le=50, description="Prescribed working sets for single-exercise calls (1–50).")] = None,
    reps: Annotated[Optional[int], Field(ge=1, le=100, description="Prescribed repetitions per set for single-exercise calls (1–100).")] = None,
    weight_kg: Annotated[Optional[float], Field(ge=0, le=500, description="Prescribed load in kg (ADDED belt load for pull-ups/chin-ups/dips; total bar load otherwise).")] = None,
    rpe: Annotated[Optional[float], Field(ge=1, le=10, description="Target RPE (1–10; inferred from 30-day e1RM envelope when omitted).")] = None,
    duration_min: Annotated[Optional[float], Field(gt=0, le=1440, description="Prescribed duration in minutes for endurance or mobility sessions.")] = None,
    distance_km: Annotated[Optional[float], Field(gt=0, le=500, description="Prescribed distance in kilometers for running, rowing, SkiErg, or cycling.")] = None,
    exercise_type: Annotated[ExerciseModality, Field(description="Planned movement modality (`strength`, `endurance`, `mobility`, `other`).")] = "strength",
    comments: Annotated[Optional[str], Field(max_length=500, description="Optional pacing target, rest interval, or technical cue.")] = None,
    sessions: Annotated[Optional[List[Dict[str, Any]]], Field(description="Batch of planned exercise dicts across one or multiple dates scheduled atomically.")] = None,
    replace: Annotated[Optional[bool], Field(description="When true, replaces existing planned exercises on covered date(s) instead of appending.")] = None,
    session_title: Annotated[Optional[str], Field(max_length=80, description="Optional planned session card header title.")] = None,
    debrief_summary: Annotated[Optional[str], Field(max_length=1200, description="Concise coaching rationale shown beneath the planned card in the STRUGGL app.")] = None,
) -> Dict[str, Any]:
    """Schedule or update PLANNED future exercises on a signed-in athlete's STRUGGL calendar across one
    or multiple dates (`replace=True` overwrites existing planned items on covered dates while leaving
    completed logs untouched), returning `saved`, `result`, `trace_id`, and `advisories`. Use only for
    upcoming workouts; to record already-completed training, use `log_workout` instead. Requires `write` scope."""
    return _request("POST", "/v1/me/workouts/plan", json=_drop_none({
        "exercise": exercise, "date": date, "sets": sets, "reps": reps, "weight_kg": weight_kg,
        "rpe": rpe, "duration_min": duration_min, "distance_km": distance_km,
        "exercise_type": exercise_type, "comments": comments, "sessions": sessions,
        "replace": replace, "session_title": session_title, "debrief_summary": debrief_summary}))


# ── Public calculators (no token) ────────────────────────────────────────────

def hyrox_pace(
    five_k: Annotated[str, Field(description="Standalone open 5 km run time as MM:SS between 12:00 and 60:00 (e.g. '21:30').")],
    goal: Annotated[Optional[str], Field(description="Optional target Hyrox finish time as H:MM:SS between 0:50:00 and 4:00:00 (e.g. '1:15:00').")] = None,
) -> Dict[str, Any]:
    """Estimate top-level Hyrox finish time, compromised pace band (`hyrox_runs`), and Riegel 10K/Half/Marathon
    `race_predictions` from a standalone 5K time. Stateless public calculator (no token required, per-IP
    fair-use rate limits). Use for quick overall finish-time estimates; for individual Lap 1–8 station-fatigued
    splits and Lap 1 blow-up cost use `hyrox_splits`, or use `hyrox_autopsy` to diagnose actual race splits."""
    return _request("GET", "/v1/public/hyrox-pace", auth=False, params={"five_k": five_k, "goal": goal})


def strength_benchmark(
    lift: Annotated[LiftName, Field(description="Supported compound lift key (`dip`, `pull_up`, `chin_up` include bodyweight in system math).")],
    weight_kg: Annotated[float, Field(ge=0, le=500, description="External load lifted in kg (ADDED belt load for `dip`, `pull_up`, `chin_up`; total bar load otherwise).")],
    reps: Annotated[int, Field(ge=1, le=20, description="Completed repetitions in the set (1–20; Wathan curve caps extrapolation beyond 10 reps).")],
    bodyweight_kg: Annotated[float, Field(ge=35, le=200, description="Athlete bodyweight in kg (35–200) for calisthenics system load and allometric scoring.")],
    sex: Annotated[Literal["male", "female"], Field(description="Biological sex reference curve (`male` or `female`) for relative strength normalization.")],
    age: Annotated[Optional[int], Field(ge=13, le=90, description="Optional athlete age in years (13–90) for masters/youth coefficient adjustment.")] = None,
) -> Dict[str, Any]:
    """Evaluate a single lifting set's piecewise Wathan `e1rm_kg`, sex/bodyweight/age-adjusted `score`
    (0–100), population `tier` (`untrained` to `elite`), and `next_tier` kg target. Stateless public
    calculator (no token required). Use to benchmark relative strength standards; to prescribe `reps @ RPE`
    working loads, barbell plate pairs, or Karvonen Zone 2 HR, use `plates_zone2` instead."""
    return _request("GET", "/v1/public/strength-benchmark", auth=False, params={
        "lift": lift, "weight_kg": weight_kg, "reps": reps, "bodyweight_kg": bodyweight_kg,
        "sex": sex, "age": age})


def interference_tax(
    sessions: Annotated[List[Dict[str, Any]], Field(description="Timestamped weekly sessions (`start` ISO-8601, `type`: 'strength'|'endurance', optional `duration_min`, `intensity`, `distance_km`, `lower_body`, `hinge`).")],
    priority: Annotated[Optional[Literal["strength", "endurance"]], Field(description="Optional training block priority (`strength` or `endurance`) weighting conflict penalties.")] = None,
) -> Dict[str, Any]:
    """Audit a multi-session weekly hybrid schedule for AMPK-mTOR `<3h`/`3–6h` proximity interference,
    `36h` glycogen depletion before legs, `48h` heavy-hinge CNS recovery, and Seiler `80/20` drift
    (returning `tax_pct`, `severity_level`, `findings`, and `recommendations`). Stateless public calculator
    (no token required). Use for cross-modal weekly timing conflicts; to audit per-muscle lifting set
    volume without endurance timing, use `volume_audit` instead."""
    return _request("POST", "/v1/public/tax", auth=False, json=_drop_none({
        "sessions": sessions, "priority": priority}))


def volume_audit(
    entries: Annotated[List[Dict[str, Any]], Field(description="Weekly movement entries (`archetype` key, `sets` count, optional `rpe` 5–10 and `frequency_days` 1–7).")],
) -> Dict[str, Any]:
    """Audit an arbitrary or hypothetical weekly lifting split across all 17 muscle groups using fractional
    set accounting (`1.0x` prime mover, `0.5x` synergist, `RPE >= 6` hard-set gate) vs MEV/MAV/MRV
    landmarks, returning `muscles`, `overloaded_muscles`, `undertrained_muscles`, and `recommendations`.
    Stateless public calculator (no token required). Use when passing movement set counts directly without
    an account; for a signed-in athlete's saved ledger volume, use `get_muscle_volume` instead."""
    return _request("POST", "/v1/public/volume-audit", auth=False, json={"entries": entries})


def hyrox_splits(
    standalone_5k_time: Annotated[str, Field(description="Standalone open 5 km run time as MM:SS (e.g. '21:30').")],
    goal_time: Annotated[Optional[str], Field(description="Optional target Hyrox finish time as H:MM:SS (e.g. '1:18:00').")] = None,
    cns_penalty_sec_per_km: Annotated[int, Field(ge=0, le=35, description="Extra sled/CNS peripheral leg-fatigue penalty in seconds per km (0–35).")] = 0,
    division: Annotated[Literal["open_men", "open_women", "pro_men", "pro_women", "doubles"], Field(description="Hyrox race category adjusting station sled/wall-ball load decay offsets.")] = "open_men",
) -> Dict[str, Any]:
    """Calculate all 8 individual `1 km` compromised Hyrox lap targets (`laps` 1–8 with preceding-station
    fatigue multipliers, Open/Pro/Doubles offsets, `est_total_race_time`, and `lap1_blowup_cost_minutes`)
    from a standalone 5K time. Stateless public calculator (no token required). Use when building a
    lap-by-lap pre-race execution plan; for a quick top-level summary use `hyrox_pace`, or use
    `hyrox_autopsy` to diagnose actual post-race splits."""
    return _request("POST", "/v1/public/hyrox-splits", auth=False, json=_drop_none({
        "standalone_5k_time": standalone_5k_time, "goal_time": goal_time,
        "cns_penalty_sec_per_km": cns_penalty_sec_per_km, "division": division}))


def plates_zone2(
    lift: Annotated[LiftName, Field(description="Target compound lift (`pull_up`, `chin_up`, and `dip` include bodyweight in system load).")] = "bench_press",
    bodyweight_kg: Annotated[float, Field(gt=35, lt=220, description="Athlete bodyweight in kg (>35 and <220), folded into weighted calisthenics load.")] = 78.0,
    sex: Annotated[Literal["male", "female"], Field(description="Biological sex (`male` or `female`).")] = "male",
    ref_weight_kg: Annotated[float, Field(ge=0, le=500, description="Reference set external load in kg (ADDED belt load for `pull_up`, `chin_up`, `dip`).")] = 100.0,
    ref_reps: Annotated[int, Field(ge=1, le=20, description="Repetitions completed in the reference set (1–20).")] = 5,
    ref_rpe: Annotated[float, Field(ge=5.0, le=10.0, description="Perceived exertion RPE of the reference set (5.0–10.0).")] = 8.5,
    target_reps: Annotated[int, Field(ge=1, le=20, description="Desired repetitions per working set to prescribe load for (1–20).")] = 8,
    target_rpe: Annotated[float, Field(ge=5.0, le=10.0, description="Desired effort RPE for the prescribed working set (5.0–10.0).")] = 8.0,
    bar_weight_kg: Annotated[float, Field(ge=10.0, le=25.0, description="Empty Olympic barbell weight in kg (20 kg standard or 15 kg women's bar).")] = 20.0,
    age: Annotated[int, Field(ge=14, le=90, description="Athlete age in years (14–90) for Tanaka HRmax (`208 - 0.7 * age`).")] = 30,
    rest_hr: Annotated[int, Field(ge=32, le=110, description="Morning resting heart rate in bpm (32–110) for Karvonen HRR zones.")] = 52,
    max_hr: Annotated[Optional[int], Field(ge=130, le=230, description="Optional measured HRmax in bpm (overrides Tanaka formula when set).")] = None,
) -> Dict[str, Any]:
    """Calculate prescribed working load (`prescribed_added_kg`, `e1rm_total_kg`) for a target `reps @ RPE`,
    exact barbell `plate_breakdown` per side, and Tanaka + Karvonen Zone 2 heart rate (`karvonen_z2_min`,
    `karvonen_z2_max` bpm). Stateless public calculator (no token required). Use for session load/plate
    prescription and Zone 2 HR targets; to rank a lift against population strength tiers (`untrained` to
    `elite`), use `strength_benchmark` instead."""
    return _request("POST", "/v1/public/plates-zone2", auth=False, json=_drop_none({
        "lift": lift, "bodyweight_kg": bodyweight_kg, "sex": sex, "ref_weight_kg": ref_weight_kg,
        "ref_reps": ref_reps, "ref_rpe": ref_rpe, "target_reps": target_reps,
        "target_rpe": target_rpe, "bar_weight_kg": bar_weight_kg, "age": age,
        "rest_hr": rest_hr, "max_hr": max_hr}))


def hyrox_autopsy(
    standalone_5k_time: Annotated[str, Field(description="Athlete's standalone open 5 km run time as MM:SS (e.g. '22:30') anchoring expected pace.")],
    run_times: Annotated[Optional[List[str]], Field(description="Optional 8 actual 1 km Hyrox run lap splits in race order as MM:SS strings.")] = None,
    total_run_time: Annotated[Optional[str], Field(description="Optional cumulative 8 km run split total as MM:SS or H:MM:SS when per-lap splits are unavailable.")] = None,
    station_times: Annotated[Optional[Dict[str, str]], Field(description="Optional actual station split times (MM:SS) keyed by `skierg`, `sled_push`, `sled_pull`, `burpees`, `row`, `farmers_carry`, `lunges`, `wall_balls`.")] = None,
    actual_finish_time: Annotated[Optional[str], Field(description="Optional official chip finish time as H:MM:SS.")] = None,
) -> Dict[str, Any]:
    """Diagnose completed or simulated Hyrox race results by comparing actual `8x1 km` run splits and 8
    station times against compromised pacing targets and P25–P75 station benchmarks (`laps_analysis`,
    `station_bottlenecks`, `recommendations`). Stateless public calculator (no token required). Use
    post-race or post-sim when actual splits exist; to project pre-race target splits from a 5K time alone,
    use `hyrox_splits` or `hyrox_pace` instead."""
    return _request("POST", "/v1/public/autopsy", auth=False, json=_drop_none({
        "standalone_5k_time": standalone_5k_time, "run_times": run_times,
        "total_run_time": total_run_time, "station_times": station_times,
        "actual_finish_time": actual_finish_time}))


TOOLS = (
    get_coaching_brief,
    get_profile,
    get_sessions,
    get_muscle_volume,
    log_workout,
    plan_workout,
    hyrox_pace,
    strength_benchmark,
    interference_tax,
    volume_audit,
    hyrox_splits,
    plates_zone2,
    hyrox_autopsy,
)
WRITE_TOOLS = {"log_workout", "plan_workout"}
_TOOL_TITLES = {
    "get_coaching_brief": "Get Unified Coaching Brief",
    "get_profile": "Get Athlete Profile & Race Goals",
    "get_sessions": "List Training Sessions",
    "get_muscle_volume": "Get Weekly 17-Muscle Volume Audit",
    "log_workout": "Log Completed Workout (Single or Batch)",
    "plan_workout": "Plan Scheduled Workout (Single or Batch)",
    "hyrox_pace": "Hyrox Pace & Race Time Summary",
    "strength_benchmark": "Strength e1RM & Population Tier Benchmark",
    "interference_tax": "Concurrent Training Interference Tax Audit",
    "volume_audit": "17-Muscle Fractional MEV/MAV/MRV Volume Audit",
    "hyrox_splits": "Hyrox 8-Lap Compromised Splits & Blow-Up Model",
    "plates_zone2": "Working Load, Barbell Plates & Karvonen Zone 2 Calculator",
    "hyrox_autopsy": "Hyrox Post-Race Split & Station Variance Autopsy",
}


def build_server():
    # mcp >= 2 (FastMCP was renamed MCPServer in 2.0); pinned in requirements-mcp.txt.
    from mcp.server.mcpserver import MCPServer
    from mcp.types import ToolAnnotations

    server = MCPServer("struggl", version="1.4.0", instructions=(
        "Struggl is a Zero-LLM-Math hybrid-athlete (Hyrox, running, strength) sports-science engine "
        "and training ledger. Call the 7 unauthenticated calculators immediately for pacing, 1RM/RPE, "
        "Zone 2 HR, 17-muscle volume audits, and interference checks. For signed-in personal coaching turns, "
        "call `get_coaching_brief(focus=...)` with a 1-sentence summary of the athlete's request, "
        "and pass multiple exercises together via `sessions=[...]` "
        "+ `debrief_summary` in a single batch `log_workout` or `plan_workout` call."))
    for fn in TOOLS:
        write = fn.__name__ in WRITE_TOOLS
        title = _TOOL_TITLES[fn.__name__]
        server.tool(
            annotations=ToolAnnotations(
                title=title,
                readOnlyHint=not write,
                destructiveHint=False,
                idempotentHint=not write,
                openWorldHint=False,
            )
        )(fn)
    return server


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
