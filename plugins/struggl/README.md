# STRUGGL — Zero-LLM-Math Hybrid Athletic Coach

**Deterministic sports-science calculators and OAuth 2.1 hybrid-athlete training ledger for Claude Code, Cowork, and Claude apps.**

Large Language Models excel at coaching empathy, habit framing, and schedule negotiation — and systematically hallucinate exercise-physiology arithmetic. Applying 1RM percentages to added belt load on weighted pull-ups while forgetting athlete bodyweight overshoots prescribed weights by 4 to 8 kg; defaulting to `220 - Age` instead of Karvonen Heart Rate Reserve under-prescribes Zone 2 aerobic training by 15 to 20 bpm; ignoring compound synergist sets masks chronic elbow and shoulder volume overload.

The **STRUGGL** plugin pairs deterministic sports-science tools hosted on the STRUGGL MCP Connector (`https://struggl.singandclap.com/v1/connector/mcp`) with two specialized coaching skills and two review agents so Claude never guesses physiological math in raw prose.

---

## What You Get

### 1. Remote MCP Connector (`https://struggl.singandclap.com/v1/connector/mcp`)
Connects over HTTPS with **OAuth 2.1 + PKCE Dynamic Client Registration** and renders interactive **MCP Apps UI cards** (`ui://struggl/coach-card.html`) directly inside Claude conversations:

| Tool | Access | What It Computes / Syncs | Literature & Model Basis |
|---|---|---|---|
| `hyrox_pace` | Read-only | Compromised Hyrox pace band, `8x1 km` run total, finish estimate & Riegel 10K / Half / Marathon | 200k-finisher speed-tier curve + Riegel (1981) |
| `hyrox_splits` | Read-only | Exact Lap 1–8 `1 km` splits (`0.94x`–`1.03x`), Pro/Doubles offsets & Lap 1 overpacing blow-up cost | 200k-finisher decay (`DOI: 10.3389/fphys.2025.1519240`) |
| `hyrox_autopsy` | Read-only | Post-race or mock-sim diagnostic: per-lap fade vs. target + P25–P75 station bottleneck leaks | Empirical station variance benchmarks |
| `strength_benchmark` | Read-only | Piecewise Wathan e1RM, sex/bodyweight/age score (`0–100`), tier & kg needed for next tier | Wathan (1994) / LeSuer et al. (1997) |
| `plates_zone2` | Read-only | Target `reps @ RPE` working weight (with bodyweight system load on pull-up/dip), barbell plates & Zone 2 bpm | Zourdos (2016) RIR + Tanaka (2001) & Karvonen (1957) HRR |
| `volume_audit` | Read-only | Weekly 17-muscle hypertrophy audit (`1.0x` prime / `0.5x` synergist, `RPE >= 6` hard-set filter) & junk volume | Schoenfeld (2017), Pelland (2024), Robinson (2024) |
| `interference_tax` | Read-only | Weekly running + lifting conflict check (`<3h`/`3–6h` AMPK-mTOR, `36h` glycogen, `48h` hinge, Seiler `80/20`) | Wilson (2012), Robineau (2016), Schumann (2022), Seiler (2010) |
| `get_profile` | Read-only | Athlete bodyweight, height, sex, primary modality, current training phase & race goals | Athlete training ledger |
| `get_sessions` | Read-only | Completed and planned training sessions over `1–90` days or a specific `YYYY-MM-DD` date | Athlete training ledger |
| `get_muscle_volume` | Read-only | Current-week effective hard sets across all 17 muscle groups against MEV / MAV / MRV landmarks | Athlete training ledger |
| `log_workout` | Write | Persist one completed strength or endurance exercise with duplicate-write protection & e1RM PR detection | Athlete training ledger |
| `plan_workout` | Write | Schedule one planned strength or endurance exercise onto the athlete's calendar (`YYYY-MM-DD`) | Athlete training ledger |

### 2. Skills (`skills/`)
- **`struggl-coach`:** Hybrid-athlete coaching workflow teaching Claude to inspect 14-day fatigue and 17-muscle weekly MEV/MAV/MRV balance before prescribing workouts, respect 48h heavy-hinge and 6h AMPK-mTOR windows, and confirm every workout write.
- **`fitness-agent-primitives`:** Reference guide for developers building fitness, running, Hyrox, or wearable AI software, explaining how to separate deterministic exercise physiology from longitudinal 30-day workload state.

### 3. Agents (`agents/`)
- **`struggl-hybrid-coach`:** Specialist subagent for weekly strength, running, and Hyrox session planning, race-split modeling, and post-session logging.
- **`fitness-math-auditor`:** Code and prompt reviewer that flags `220 - Age` heart-rate bugs, missing weighted-calisthenics bodyweight loads, unfiltered warm-up set counting, and rolling boxcar ACWR spikes.

---

## Authentication, Data Handling & Privacy

- **Declared Server Only:** All MCP tool calls go exclusively to `https://struggl.singandclap.com/v1/connector/mcp` over TLS (`HTTPS`). No skills, agents, or hooks send data to any third-party endpoint or read credentials from your local environment.
- **OAuth 2.1 + PKCE:** When you connect STRUGGL in Claude, browser sign-in uses OAuth 2.1 Dynamic Client Registration (`read` and `write` scopes) on [https://struggl.singandclap.com/connect](https://struggl.singandclap.com/connect). You can revoke access at any time from your STRUGGL account settings.
- **Data Sent & Stored:** Calculator tools (`hyrox_pace`, `hyrox_splits`, `hyrox_autopsy`, `strength_benchmark`, `plates_zone2`, `volume_audit`, `interference_tax`) process only the numerical exercise parameters passed in the tool call. Ledger tools read your athlete profile, race goals, and workout sessions, and write completed or planned workouts only when you ask Claude to log or schedule them. Raw Apple HealthKit and Android Health Connect sensor records are never exposed through external connectors.
- **Links & Support:**
  - **Privacy Policy:** [https://struggl.singandclap.com/privacy](https://struggl.singandclap.com/privacy)
  - **Terms of Service:** [https://struggl.singandclap.com/terms](https://struggl.singandclap.com/terms)
  - **API & Connector Documentation:** [https://struggl.singandclap.com/v1/connector/docs](https://struggl.singandclap.com/v1/connector/docs)
  - **Account & Support:** [https://struggl.singandclap.com/connect](https://struggl.singandclap.com/connect) (`taha@tbaziz.com`)

## License

Apache License 2.0 — see `LICENSE` and `NOTICE`. Published by **Sing And Clap SASU** ([https://struggl.singandclap.com](https://struggl.singandclap.com)).
