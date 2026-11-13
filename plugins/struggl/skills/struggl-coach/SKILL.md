---
name: struggl-coach
description: Zero-LLM-Math hybrid-athlete (strength, running, Hyrox, ATHX) sports-science workflow powered by STRUGGL MCP. Activate whenever the user mentions lifting, running, Hyrox, Zone 2 heart rate, 1RM, RPE, barbell plates, weekly muscle volume (MEV/MAV/MRV), concurrent training interference, workout logging, or slotting training around coding blocks.
license: Apache-2.0
compatibility: Works across Claude Code, Cowork, and Claude apps via the STRUGGL OAuth 2.1 MCP Connector (https://struggl.singandclap.com/v1/connector/mcp).
metadata:
  author: Sing And Clap SASU
  version: "1.3.1"
  homepage: https://struggl.singandclap.com/connect
---

# STRUGGL Hybrid Coach Skill (Zero-LLM-Math)

STRUGGL (`https://struggl.singandclap.com`) separates conversational coaching from exercise-physiology arithmetic. **Never estimate 1RM, RPE working loads, weighted-calisthenics system loads, Zone 2 bpm, Hyrox run splits, weekly muscle sets, or AMPK-mTOR interference in raw LLM prose** — call the deterministic STRUGGL MCP tools on `https://struggl.singandclap.com/v1/connector/mcp` instead.

## 1. Sports-Science Calculators (7 Deterministic Tools)

| User Question / Intent | MCP Tool to Call | Underlying Science Model |
|---|---|---|
| Quick Hyrox pace band + 10k / Half / Marathon Riegel predictions from a 5K time | `hyrox_pace` | 200k-finisher speed-tier decay + Riegel curve |
| Full Lap 1–8 Hyrox 1 km splits, Pro/Doubles offset & Lap 1 overpacing blow-up cost | `hyrox_splits` | Piecewise decay (`+17.2%` to `+24.0%`) + per-lap fatigue (`0.94x`–`1.03x`) |
| Post-race or mock-sim Hyrox split & station leak diagnostic | `hyrox_autopsy` | Lap fade detection + P25–P75 station variance benchmarks |
| e1RM, sex/bodyweight/age strength score (`0–100`), tier & kg to next tier | `strength_benchmark` | Piecewise Wathan (1994) + total system load on `pull_up` / `chin_up` / `dip` |
| Exact working weight for target `reps @ RPE`, gym barbell plates/side & Zone 2 HR | `plates_zone2` | Wathan + Zourdos (2016) RIR + Tanaka (2001) & Karvonen (1957) HRR |
| Weekly program audit across all 17 muscle groups + junk-volume detection | `volume_audit` | `1.0x` prime / `0.5x` synergist, `RPE >= 6` hard-set gate, MEV/MAV/MRV |
| Weekly running + lifting schedule conflict check (AMPK-mTOR, glycogen, hinge DOMS) | `interference_tax` | `<3h` / `3–6h` proximity, `36h` long-run glycogen, `48h` hinge, Seiler 80/20 |

For exact parameter enums (including all 17 `volume_audit` movement archetypes and `station_times` keys), read `./references/science_tools_schema.md`.

## 2. Personal Training Ledger (5 OAuth 2.1 Tools)

When the athlete wants to inspect their real history, check current-week fatigue, or log/schedule workouts (`get_profile`, `get_sessions`, `get_muscle_volume`, `log_workout`, `plan_workout`):

- Authenticate via **OAuth 2.1 + PKCE** through the `struggl` MCP Connector (`https://struggl.singandclap.com/v1/connector/mcp`). In Claude Code, run `/mcp` and select **Authenticate** on `struggl`; in Claude apps and Cowork, click **Connect** when prompted.
- New athletes can create a STRUGGL account at `https://struggl.singandclap.com/connect`.

## 3. Daily Hybrid Coaching Rules

1. **Read Before Prescribing:** Always call `get_profile()`, `get_sessions(days=14)`, and `get_muscle_volume()` before prescribing personal exercises or weights. Target muscles sitting below MAV while respecting the 48h heavy-hinge and 6h AMPK-mTOR windows.
2. **Explicit Confirmation on Writes:**
   - Call `log_workout` **only** for exercises the athlete confirms they completed, **once per exercise**.
   - Call `plan_workout` **only** when the athlete asks to schedule on their calendar (`date="YYYY-MM-DD"`), **once per exercise**.
   - For `dip`, `pull_up`, and `chin_up`, `weight_kg` is always the **added belt load** (`0` for bodyweight).
3. **Concise Coaching Synthesis:** The STRUGGL connector automatically attaches interactive MCP Apps UI cards (`ui://struggl/coach-card.html`) in Claude clients that render MCP Apps. Keep your prose synthesis focused on 2–4 actionable coaching takeaways rather than repeating raw JSON tables verbatim.
