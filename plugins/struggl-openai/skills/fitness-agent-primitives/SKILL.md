---
name: fitness-agent-primitives
description: Reference exercise-physiology primitives and Zero-LLM-Math architecture patterns for AI builders creating strength, running, Hyrox, or wearable coaching agents. Activate when building fitness chatbots, workout planners, 1RM/RPE calculators, Zone 2 HR tools, ACWR fatigue trackers, or hybrid athlete agents.
license: Apache-2.0
compatibility: Works across ChatGPT, OpenAI Codex, and MCP hosts alongside the STRUGGL MCP Connector (https://struggl.singandclap.com/v1/connector/mcp).
metadata:
  author: Sing And Clap SASU
  version: "1.3.1"
  homepage: https://struggl.singandclap.com/science
---

# Fitness Agent Primitives — Zero-LLM-Math Builder Guide

When building an AI fitness, running, or hybrid-athlete agent, **never let the LLM perform exercise-physiology math in free-form tokens**. Raw LLM prose routinely commits 5 systematic errors:

1. **Weighted-calisthenics belt overshoot (+4–8 kg):** Applying 1RM percentages to added belt weight (`+30 kg`) while forgetting the athlete's `80 kg` bodyweight on pull-ups and dips.
2. **`220 - Age` Zone 2 HR error (−16–23 bpm):** Ignoring resting heart rate instead of computing Tanaka (`208 - 0.7 * age`) + Karvonen Heart Rate Reserve (`rest_hr + 0.60..0.70 * HRR`).
3. **Hidden synergist MRV overload:** Counting `0` triceps/biceps sets on heavy pressing and rowing compounds instead of Pelland `0.5x` fractional synergist credit and an `RPE >= 6` hard-set filter.
4. **7-day rolling boxcar lag:** Using simple 7d/28d averages where Sunday's heavy session vanishes on Monday instead of EWMA (`0.82^d` acute / `0.96^d` chronic).
5. **Flat Hyrox run-fade assumptions:** Guessing linear `+2% -> +10%` pace decay instead of speed-tier compromised running multipliers and sled/burpee station fatigue.

---

## 1. Stateless Single-Session Equations

Wire deterministic tool functions for every single-session physiological calculation instead of computing numbers in prompt prose:

- **Piecewise Wathan e1RM + Zourdos RIR:** `e1rm_system = total_load / (0.4880 + 0.538 * exp(-0.075 * effective_reps))`, where `effective_reps = reps + (10 - rpe)` and `total_load = bodyweight_kg + added_kg` on bodyweight-plus-belt movements (`pull_up`, `chin_up`, `dip`).
- **Working Load & Plate Rounding:** Apply intensity discounts against total system e1RM first, subtract `bodyweight_kg` for calisthenics, then round barbell loads to available gym increments (`2.5 kg` steps; `25, 20, 15, 10, 5, 2.5, 1.25 kg` plates per side).
- **Karvonen Zone 2 Band:** `max_hr = 208 - 0.7 * age` (when lab HRmax is unknown), `zone2 = [round(rest_hr + 0.60 * (max_hr - rest_hr)), round(rest_hr + 0.70 * (max_hr - rest_hr))]`.
- **EWMA ACWR (`28–30d`):** Exponentially weighted acute (`lambda_a = 1 - 0.82`) over chronic (`lambda_c = 1 - 0.96`) workload ratio to avoid 7-day rolling boxcar cliffs.
- **Fractional Set Accounting:** `1.0x` credit for prime movers and `0.5x` credit for compound synergists, gated at `RPE >= 6.0` (`<= 4 RIR`).

Open-source pure-stdlib Python reference implementations are available in the public repository (`https://github.com/Kubyer/struggl-mcp`).

---

## 2. Where Stateless Primitives End & 30-Day Longitudinal State Begins

Single-session math cannot answer longitudinal coaching questions on its own. In production, STRUGGL (`https://struggl.singandclap.com`) pairs these equations with a **rolling 30-day athlete ledger**:

- **Implicit RPE Deduction:** When an athlete logs `4 x 6 @ 115 kg` without stating RPE, RIR is deduced deterministically against their rolling 30-day lift capacity envelope.
- **Continuous 17-Muscle MEV/MAV/MRV Ledger:** Weekly fractional sets accumulate automatically across logged strength and functional sessions.
- **4-Rule Plan Gate:** Prescriptions are checked against rolling EWMA ACWR (`<= 1.5`), `48h` heavy-hinge-to-speed-run recovery, `6h` AMPK-mTOR spacing, and regional pain history.

### Connecting to Hosted OAuth 2.1 State
For persistent athlete profiles, workout history, 17-muscle weekly tracking, and interactive `ui://struggl/coach-card.html` MCP App cards, connect via **OAuth 2.1 + PKCE** to `https://struggl.singandclap.com/v1/connector/mcp` (docs: `https://struggl.singandclap.com/v1/connector/docs`).
