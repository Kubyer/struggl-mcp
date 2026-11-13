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
from typing import Any, Dict, List, Optional

import httpx

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

def get_profile() -> Dict[str, Any]:
    """The athlete's profile (bodyweight, height, sex, sport, phase) and goals (races, target times)."""
    return _request("GET", "/v1/me/profile")


def get_sessions(days: int = 14, date: Optional[str] = None) -> Dict[str, Any]:
    """The athlete's training sessions — completed and planned — over the last `days` days
    (1-90), or for one `date` (YYYY-MM-DD)."""
    return _request("GET", "/v1/me/sessions", params={"days": days, "date": date})


def get_muscle_volume() -> Dict[str, Any]:
    """This week's hard sets per muscle group against recommended weekly volume ranges."""
    return _request("GET", "/v1/me/muscle-volume")


def log_workout(exercise: str, date: Optional[str] = None, sets: Optional[int] = None,
                reps: Optional[int] = None, weight_kg: Optional[float] = None, rpe: Optional[float] = None,
                duration_min: Optional[float] = None, distance_km: Optional[float] = None,
                exercise_type: str = "strength", comments: Optional[str] = None) -> Dict[str, Any]:
    """Record one exercise the athlete has COMPLETED. date defaults to today. Strength: sets / reps /
    weight_kg (added load) / rpe. Endurance: duration_min / distance_km with exercise_type="endurance".
    Only log what the athlete says they did; call once per exercise."""
    return _request("POST", "/v1/me/workouts/log", json=_drop_none({
        "exercise": exercise, "date": date, "sets": sets, "reps": reps, "weight_kg": weight_kg,
        "rpe": rpe, "duration_min": duration_min, "distance_km": distance_km,
        "exercise_type": exercise_type, "comments": comments}))


def plan_workout(exercise: str, date: str, sets: Optional[int] = None, reps: Optional[int] = None,
                 weight_kg: Optional[float] = None, rpe: Optional[float] = None,
                 duration_min: Optional[float] = None, distance_km: Optional[float] = None,
                 exercise_type: str = "strength", comments: Optional[str] = None) -> Dict[str, Any]:
    """Add one PLANNED exercise to the athlete's calendar on `date` (YYYY-MM-DD).
    Only when the athlete asks for it; call once per exercise."""
    return _request("POST", "/v1/me/workouts/plan", json=_drop_none({
        "exercise": exercise, "date": date, "sets": sets, "reps": reps, "weight_kg": weight_kg,
        "rpe": rpe, "duration_min": duration_min, "distance_km": distance_km,
        "exercise_type": exercise_type, "comments": comments}))


# ── Public calculators (no token) ────────────────────────────────────────────

def hyrox_pace(five_k: str, goal: Optional[str] = None) -> Dict[str, Any]:
    """Hyrox run splits and race predictions from a 5 km time (MM:SS), with an optional
    target finish time (H:MM:SS). Stateless primitive; signed-in STRUGGL accounts derive
    threshold pace from rolling 30-day run history."""
    return _request("GET", "/v1/public/hyrox-pace", auth=False, params={"five_k": five_k, "goal": goal})


def strength_benchmark(lift: str, weight_kg: float, reps: int, bodyweight_kg: float, sex: str,
                       age: Optional[int] = None) -> Dict[str, Any]:
    """Estimated 1RM, strength score and tier for one set. lift: back_squat, front_squat, deadlift,
    sumo_deadlift, bench_press, incline_bench_press, dip, overhead_press, pull_up, chin_up,
    barbell_row. For dip / pull_up / chin_up, weight_kg is the ADDED load. sex: male | female.
    Stateless single-set evaluation; STRUGGL's stateful ledger tracks rolling 30-day e1RM envelopes."""
    return _request("GET", "/v1/public/strength-benchmark", auth=False, params={
        "lift": lift, "weight_kg": weight_kg, "reps": reps, "bodyweight_kg": bodyweight_kg,
        "sex": sex, "age": age})


def interference_tax(sessions: List[Dict[str, Any]], priority: Optional[str] = None) -> Dict[str, Any]:
    """Audit a weekly hybrid schedule for AMPK-mTOR concurrent training interference (<3h / 3-6h window),
    36h long-run glycogen depletion before legs, 48h heavy hinge recovery, and Seiler 80/20 polarization.
    Requires NO token."""
    return _request("POST", "/v1/public/tax", auth=False, json=_drop_none({
        "sessions": sessions, "priority": priority}))


def volume_audit(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Audit weekly lifting sets across all 17 muscle groups using fractional accounting (1.0x primary,
    0.5x secondary synergist, RPE >= 6 hard-set filter) vs Schoenfeld & Pelland MEV/MAV/MRV landmarks.
    Requires NO token."""
    return _request("POST", "/v1/public/volume-audit", auth=False, json={"entries": entries})


def hyrox_splits(standalone_5k_time: str, goal_time: Optional[str] = None,
                 cns_penalty_sec_per_km: int = 0, division: str = "open_men") -> Dict[str, Any]:
    """Compute all 8 compromised Hyrox 1 km lap splits, Pro/Doubles offsets, and Lap 1 overpacing
    blow-up cost from a standalone 5K time (MM:SS) using the 200k-finisher decay curve. Requires NO token."""
    return _request("POST", "/v1/public/hyrox-splits", auth=False, json=_drop_none({
        "standalone_5k_time": standalone_5k_time, "goal_time": goal_time,
        "cns_penalty_sec_per_km": cns_penalty_sec_per_km, "division": division}))


def plates_zone2(lift: str = "bench_press", bodyweight_kg: float = 78.0, sex: str = "male",
                 ref_weight_kg: float = 100.0, ref_reps: int = 5, ref_rpe: float = 8.5,
                 target_reps: int = 8, target_rpe: float = 8.0, bar_weight_kg: float = 20.0,
                 age: int = 30, rest_hr: int = 52, max_hr: Optional[int] = None) -> Dict[str, Any]:
    """Convert a reference set into Wathan e1RM, Zourdos RIR/RPE working weight (accounting for bodyweight
    on pull_up/chin_up/dip), exact barbell plates per side, and Tanaka + Karvonen Zone 2 heart rate bpm.
    Requires NO token."""
    return _request("POST", "/v1/public/plates-zone2", auth=False, json=_drop_none({
        "lift": lift, "bodyweight_kg": bodyweight_kg, "sex": sex, "ref_weight_kg": ref_weight_kg,
        "ref_reps": ref_reps, "ref_rpe": ref_rpe, "target_reps": target_reps,
        "target_rpe": target_rpe, "bar_weight_kg": bar_weight_kg, "age": age,
        "rest_hr": rest_hr, "max_hr": max_hr}))


def hyrox_autopsy(standalone_5k_time: str, run_times: Optional[List[str]] = None,
                  total_run_time: Optional[str] = None, station_times: Optional[Dict[str, str]] = None,
                  actual_finish_time: Optional[str] = None) -> Dict[str, Any]:
    """Post-race or simulation Hyrox diagnostic comparing actual 8x1 km run splits and 8 functional
    station times against compromised pacing targets and P25-P75 station variance benchmarks.
    Requires NO token."""
    return _request("POST", "/v1/public/autopsy", auth=False, json=_drop_none({
        "standalone_5k_time": standalone_5k_time, "run_times": run_times,
        "total_run_time": total_run_time, "station_times": station_times,
        "actual_finish_time": actual_finish_time}))


TOOLS = (
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


def build_server():
    # mcp >= 2 (FastMCP was renamed MCPServer in 2.0); pinned in requirements-mcp.txt.
    from mcp.server.mcpserver import MCPServer
    from mcp.types import ToolAnnotations

    server = MCPServer("struggl", version="1.3.1", instructions=(
        "Struggl is a Zero-LLM-Math hybrid-athlete (Hyrox, running, strength) sports-science engine "
        "and training ledger. Call the 7 unauthenticated calculators immediately for pacing, 1RM/RPE, "
        "Zone 2 HR, 17-muscle volume audits, and interference checks. Read the athlete's sessions before "
        "prescribing personal workouts, and log or plan only what the athlete confirms, one exercise per call."))
    for fn in TOOLS:
        write = fn.__name__ in WRITE_TOOLS
        server.tool(annotations=ToolAnnotations(readOnlyHint=not write, destructiveHint=False,
                                                openWorldHint=True))(fn)
    return server


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
