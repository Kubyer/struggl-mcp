# STRUGGL MCP Tools — Parameter & Literature Reference

All 12 tools below are served by the declared STRUGGL MCP Connector (`https://struggl.singandclap.com/v1/connector/mcp`).

## Part 1: 7 Deterministic Sports-Science Calculators

### 1. `hyrox_pace`
- **Inputs:** `five_k` (`MM:SS`, required, e.g. `"21:30"`), `goal` (`H:MM:SS`, optional, e.g. `"1:15:00"`).
- **Returns:** Compromised Hyrox run pace band, total `8x1 km` run time, estimated whole-race finish time, and Riegel predictions for 10K, Half-Marathon, and Marathon.

### 2. `hyrox_splits`
- **Inputs:**
  - `standalone_5k_time`: `MM:SS` (`12:00`–`60:00`, e.g. `"21:30"`)
  - `goal_time`: optional `H:MM:SS` (`0:45:00`–`3:00:00`)
  - `cns_penalty_sec_per_km`: integer `0`–`35` (default `0`)
  - `division`: `"open_men"` | `"open_women"` | `"pro_men"` | `"pro_women"` | `"doubles"`
- **Returns:** Exact target pace for Laps 1–8 (`0.94x, 0.97x, 1.00x, 1.01x, 1.03x, 1.02x, 1.01x, 1.02x`), preceding station fatigue context, and quantified **Lap 1 Trap** overpacing time loss across Laps 4–7.
- **DOI:** `10.3389/fphys.2025.1519240`

### 3. `hyrox_autopsy`
- **Inputs:**
  - `standalone_5k_time`: `MM:SS`
  - `run_times`: optional array of 8 `MM:SS` strings (Runs 1–8)
  - `total_run_time`: optional `MM:SS` or `H:MM:SS`
  - `station_times`: optional object mapping station keys (`skierg`, `sled_push`, `sled_pull`, `burpees`, `row`, `farmers_carry`, `lunges`, `wall_balls`) to `MM:SS`
  - `actual_finish_time`: optional `H:MM:SS`
- **Returns:** Per-lap status (`surged` / `on_pace` / `faded`), compromised running tax in seconds, station bottleneck ratings (`Strong` / `Minor Leak` / `Major Bottleneck`), and Braille pace sparkline.

### 4. `strength_benchmark`
- **Inputs:**
  - `lift`: `"back_squat"` | `"front_squat"` | `"deadlift"` | `"sumo_deadlift"` | `"bench_press"` | `"incline_bench_press"` | `"dip"` | `"overhead_press"` | `"pull_up"` | `"chin_up"` | `"barbell_row"`
  - `weight_kg`: `0`–`500` (**ADDED** external load for `dip`, `pull_up`, `chin_up`)
  - `reps`: `1`–`20`
  - `bodyweight_kg`: `35`–`200`
  - `sex`: `"male"` | `"female"`
  - `age`: optional `13`–`90`
- **Returns:** Piecewise Wathan e1RM, normalized `0–100` score, tier (`untrained` -> `novice` -> `intermediate` -> `proficient` -> `advanced` -> `exceptional` -> `elite`), and exact kg needed for the next tier.
- **DOI:** `10.1519/00124278-199711000-00001` (LeSuer et al., 1997 / Wathan, 1994)

### 5. `plates_zone2`
- **Inputs:** `lift`, `bodyweight_kg`, `sex`, `ref_weight_kg`, `ref_reps`, `ref_rpe` (`5.0`–`10.0`), `target_reps`, `target_rpe` (`5.0`–`10.0`), `bar_weight_kg` (`20.0` or `15.0`), `age` (`14`–`90`), `rest_hr` (`32`–`110`), optional `max_hr` (`130`–`230`).
- **Returns:** Total & added prescribed working weight, exact gym plate pairs per side (`25, 20, 15, 10, 5, 2.5, 1.25 kg`), `6x6` RPE x Reps reference table, plus Tanaka (`208 - 0.7 * Age`) + Karvonen Heart Rate Reserve Zone 2 bpm vs. naive `220 - Age` watch zones.
- **DOIs:** `10.1519/JSC.0000000000001049` (Zourdos et al., 2016), `10.1016/S0735-1097(00)01054-8` (Tanaka et al., 2001)

### 6. `volume_audit`
- **Inputs:** `entries` — array of `{ "archetype": "<key>", "sets": 0..60, "rpe": 5.0..10.0, "frequency_days": 1..7 }`.
- **17 Valid `archetype` Keys:**
  - Upper Push: `horizontal_press`, `incline_press`, `chest_fly`, `vertical_press`, `lateral_raise`, `triceps_extension`
  - Upper Pull: `vertical_pull`, `horizontal_row`, `shrug_carry`, `biceps_curl`
  - Lower & Trunk: `squat_lunge`, `hip_hinge`, `leg_isolation`, `hip_abduction_adduction`, `calves`, `core_abs`, `neck_work`
- **Returns:** Effective weekly hard sets across all 17 muscles (`CHEST`, `LATS`, `UPPER_BACK`, `TRAPS`, `SHOULDERS`, `BICEPS`, `TRICEPS`, `FOREARMS`, `QUADRICEPS`, `HAMSTRINGS`, `GLUTES`, `CALVES`, `ABDOMINALS`, `LOWER_BACK`, `ABDUCTORS`, `ADDUCTORS`, `NECK`), junk sets above MRV, deficits below MEV, and reallocation recommendations.
- **DOIs:** `10.1080/02640414.2016.1210197` (Schoenfeld et al., 2017), `10.51224/SRXIV.460` (Pelland et al., 2024), `10.1007/s40279-024-02069-2` (Robinson et al., 2024)

### 7. `interference_tax`
- **Inputs:**
  - `sessions`: array of `{ "start": "YYYY-MM-DDTHH:MM:SS", "type": "strength" | "endurance", "duration_min": 60, "intensity": "light" | "moderate" | "heavy" | "easy" | "hard", "modality": "run", "distance_km": 10.0, "lower_body": true, "hinge": false, "explosive": false, "max_test": false }`
  - `priority`: optional `"strength"` | `"endurance"`
- **Returns:** Interference Tax (`0–40%`), CNS strain score (`1–10`), rule-level violations (`<3h` / `3–6h` proximity, `36h` glycogen depletion before legs, `48h` heavy hinge before quality run, back-to-back hard runs, Seiler `80/20` drift), and actionable fixes.
- **DOIs:** `10.1519/JSC.0b013e31823a3e2d` (Wilson et al., 2012), `10.1519/JSC.0000000000000798` (Robineau et al., 2016), `10.1007/s40279-021-01587-7` (Schumann et al., 2022), `10.1123/ijspp.5.3.276` (Seiler, 2010)

---

## Part 2: 5 OAuth 2.1 Personal Ledger Tools

1. `get_profile` (`read`): Biometrics, primary modality, training phase, and target race calendar.
2. `get_sessions` (`read`): Completed and scheduled workouts over `days` (`1–90`, default `14`) or `date` (`YYYY-MM-DD`).
3. `get_muscle_volume` (`read`): Live current-week 17-muscle hard-set ledger from logged workouts.
4. `log_workout` (`write`): Persist one completed exercise with arg-keyed duplicate-write protection and automatic e1RM PR detection.
5. `plan_workout` (`write`): Schedule one planned exercise on `date` (`YYYY-MM-DD`).
