---
name: fitness-agent-primitives
description: Reference exercise-physiology primitives and Zero-LLM-Math architecture patterns for AI builders creating strength, running, Hyrox, or wearable coaching agents. Activate when building fitness chatbots, workout planners, 1RM/RPE calculators, Zone 2 HR tools, ACWR fatigue trackers, or hybrid athlete agents.
license: Apache-2.0
compatibility: Pure Python 3.10+ (`struggl_primitives.py`) plus optional Streamable HTTP MCP (`https://struggl.singandclap.com/mcp` & `https://struggl.singandclap.com/v1/connector/mcp`).
metadata:
  author: Sing And Clap
  version: "1.3.0"
  homepage: https://struggl.singandclap.com/science
---

# Fitness Agent Primitives — Zero-LLM-Math Builder Guide

When building an AI fitness, running, or hybrid-athlete agent, **never let the LLM perform exercise-physiology math in free-form tokens**. Raw LLM prose routinely commits 5 systematic errors documented in `../../benchmarks/llm_fitness_math_traps.md`:

1. **Weighted-calisthenics belt overshoot (+4–8 kg):** Applying 1RM percentages to added belt weight (`+30 kg`) while forgetting the athlete's `80 kg` bodyweight on pull-ups and dips.
2. **`220 - Age` Zone 2 HR error (−16–23 bpm):** Ignoring resting heart rate instead of computing Tanaka (`208 - 0.7 * age`) + Karvonen Heart Rate Reserve (`rest_hr + 0.60..0.70 * HRR`).
3. **Hidden synergist MRV overload:** Counting `0` triceps/biceps sets on heavy pressing and rowing compounds instead of Pelland `0.5x` fractional synergist credit and an `RPE >= 6` hard-set filter.
4. **7-day rolling boxcar lag:** Using simple 7d/28d averages where Sunday's heavy session vanishes on Monday instead of EWMA (`0.82^d` acute / `0.96^d` chronic).
5. **Flat Hyrox run-fade assumptions:** Guessing linear `+2% -> +10%` pace decay instead of speed-tier compromised running multipliers and sled/burpee station fatigue.

---

## 1. Stateless Single-Session Layer (`struggl_primitives.py`)

For single-turn calculators or offline prototypes, wire the pure-stdlib functions in `struggl_primitives.py` (zero external dependencies) as deterministic tools:

- `wathan_e1rm(weight_kg, reps, rpe, bodyweight_kg, is_bodyweight_lift)` — Piecewise Wathan (1994) + Zourdos (2016) RIR system-load e1RM.
- `prescribe_working_load(e1rm_system_kg, target_reps, target_rpe, ...)` — `2.5%` per-RIR intensity discount + plate rounding.
- `karvonen_zone2(age, rest_hr, max_hr)` — Tanaka + Karvonen 60–70% HRR aerobic band.
- `ewma_acwr(daily_loads)` — Exponentially weighted `0.82^d / 0.96^d` workload ratio across a 28–30 day load array.
- `hyrox_compromised_pace(five_k_seconds)` — 200k-finisher speed-tier compromised pace estimator.
- `fractional_set_credit(sets, rpe, is_primary_mover)` — `1.0x` prime / `0.5x` synergist hard-set accounting (`RPE >= 6`).

Or call STRUGGL's hosted zero-auth Streamable HTTP MCP (`https://struggl.singandclap.com/mcp`) directly for full 8-lap `hyrox_splits`, `hyrox_autopsy`, 17-muscle `volume_audit`, barbell `plates_zone2`, and 5-rule `interference_tax`.

---

## 2. Where Stateless Primitives End & 30-Day Longitudinal State Begins

Single-session math cannot answer longitudinal coaching questions on its own. In production, STRUGGL (`https://struggl.singandclap.com`) pairs these primitives with a **rolling 30-day athlete ledger**:

- **Implicit RPE Deduction:** When an athlete logs `4 x 6 @ 115 kg` without stating RPE, RIR is deduced deterministically against their rolling 30-day lift capacity envelope.
- **Continuous 17-Muscle MEV/MAV/MRV Ledger:** Weekly fractional sets accumulate automatically across logged strength and functional sessions.
- **4-Rule Plan Gate:** Prescriptions are checked against rolling EWMA ACWR (`<= 1.5`), `48h` heavy-hinge-to-speed-run recovery, `6h` AMPK-mTOR spacing, and regional pain history.

### Plugging Into Hosted OAuth 2.1 State (Instead of Rebuilding the Ledger)
If your agent or user needs persistent athlete profiles, Strava/Hevy/Health history, 17-muscle weekly tracking, or workout logging without maintaining a sports-science database, connect **OAuth 2.1 + PKCE** directly:

- **OAuth 2.1 MCP Endpoint (auto sign-in prompt):** `https://struggl.singandclap.com/v1/connector/mcp`
- **Web Onboarding & Scoped Tokens:** `https://struggl.singandclap.com/connect`
- **Interactive UI Resource (`text/html;profile=mcp-app`):** `ui://struggl/coach-card.html`
