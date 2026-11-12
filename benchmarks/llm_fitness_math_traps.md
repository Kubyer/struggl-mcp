# Why Raw LLMs Fail Exercise Physiology Math: 5 Reproducible Traps

Large Language Models excel at coaching empathy, habit framing, and schedule negotiation — **and systematically hallucinate exercise-science arithmetic**.

Below are **5 reproducible physiological math failure modes** observed when prompting frontier coding and chat models without deterministic tools, paired with the exact outputs and peer-reviewed equations computed by the zero-auth **STRUGGL MCP** calculators (`https://struggl.singandclap.com/mcp`).

---

## Summary Benchmark Table

| # | Physiological Trap | Prompted Scenario | Typical Raw LLM Output | STRUGGL Deterministic Output (`POST /mcp`) | Real-World Consequence of Raw LLM Error |
|---|---|---|---|---|---|
| **1** | **Weighted Calisthenics System Load** | `80 kg` athlete does `5` pull-ups @ `+30 kg` (`RPE 9`); wants belt load for `8 reps @ RPE 8` | `+22.5 kg` belt (`~75%` of `30 kg` external weight only) | **`+17.5 kg` belt** (`97.5 kg` total system load on `132.4 kg` Wathan e1RM) | **`+5.0 kg` overshoot** — athlete fails on rep 5–6 instead of hitting 8 @ 2 RIR |
| **2** | **`220 - Age` vs. Karvonen HRR Zone 2** | `35` yo hybrid athlete, resting HR `48 bpm`, asks for Zone 2 HR | `111–130 bpm` (`60–70%` of `220 - 35`) | **`130–143 bpm`** (Tanaka `184` HRmax + Karvonen `60–70%` HRR) | **`19 bpm` under-prescription** — athlete shuffles in Zone 1 instead of training aerobic threshold |
| **3** | **Flat Hyrox Pacing & Lap 1 Trap** | `20:00` standalone 5K (`4:00/km`) runner asks for `8x1 km` Hyrox splits | Even `4:15–4:20/km` across all 8 laps | **`4:46/km` avg (`+19.0%` decay)**: Lap 1 `4:28/km` -> Lap 5 `4:54/km` | **`~6.2 min` blow-up** across Laps 4–7 (Sled Pull -> Lunges) from early lactate spike |
| **4** | **Synergist Blindness & Warm-Up Sets** | `10` Bench + `8` Incline + `8` OHP + `10` Triceps (`RPE 8.5–9`) + `4` Squat @ `RPE 5.5` | `"10 Triceps sets (optimal), 4 Quad sets"` | **`23.0` Triceps hard sets (`+5.0` Junk Sets > `18` MRV)**; **`0.0` Quad hard sets** | Chronic elbow tendinopathy from hidden pressing volume + zero quad hypertrophy stimulus (`>4 RIR`) |
| **5** | **Concurrent AMPK–mTOR & Hinge Clock** | `07:00` `95m` run -> `09:00` heavy RDL/Squat -> next-day `07:00` track intervals | *"Solid hybrid grind — fuel with carbs!"* | **`16.5%` Interference Tax (`Moderate`)**: `<3h` AMPK-mTOR violation + `<48h` hinge conflict | Blunted myofibrillar protein synthesis + `+3–7%` running oxygen cost on track intervals |

---

## Reproducing All 5 Cases Over Zero-Auth MCP (`curl`)

Every command below hits the public stateless Streamable HTTP MCP endpoint (`https://struggl.singandclap.com/mcp`) with **no API key or account**.

### Trap 1 & 2 — System Load (`pull_up`) + Tanaka/Karvonen Zone 2 (`plates_zone2`)
- **Literature:** Wathan (1994) / LeSuer et al. (1997, `DOI: 10.1519/00124278-199711000-00001`), Zourdos et al. (2016, `DOI: 10.1519/JSC.0000000000001049`), Tanaka et al. (2001, `DOI: 10.1016/S0735-1097(00)01054-8`), Karvonen et al. (1957, `PMID: 13470504`).

```bash
curl -sS https://struggl.singandclap.com/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "plates_zone2",
      "arguments": {
        "lift": "pull_up",
        "bodyweight_kg": 80,
        "sex": "male",
        "ref_weight_kg": 30,
        "ref_reps": 5,
        "ref_rpe": 9.0,
        "target_reps": 8,
        "target_rpe": 8.0,
        "age": 35,
        "rest_hr": 48
      }
    }
  }'
```

### Trap 3 — Speed-Tier Hyrox Compromised Pacing (`hyrox_splits`)
- **Literature:** Frontiers in Physiology Hyrox determinants (`DOI: 10.3389/fphys.2025.1519240`) + STRUGGL 200,000-finisher piecewise decay curve (`0.94x` Lap 1 start multiplier to `1.03x` Lap 5 post-Burpee Broad Jump peak).

```bash
curl -sS https://struggl.singandclap.com/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "hyrox_splits",
      "arguments": {
        "standalone_5k_time": "20:00",
        "division": "open_men"
      }
    }
  }'
```

### Trap 4 — Fractional `1.0x / 0.5x` Volume & `RPE >= 6` Proximity Gate (`volume_audit`)
- **Literature:** Schoenfeld, Ogborn & Krieger (2017, `DOI: 10.1080/02640414.2016.1210197`), Pelland et al. (2024, `DOI: 10.51224/SRXIV.460`), Robinson et al. (2024, `DOI: 10.1007/s40279-024-02069-2`).

```bash
curl -sS https://struggl.singandclap.com/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "volume_audit",
      "arguments": {
        "entries": [
          {"archetype": "horizontal_press", "sets": 10, "rpe": 8.5},
          {"archetype": "incline_press", "sets": 8, "rpe": 8.5},
          {"archetype": "vertical_press", "sets": 8, "rpe": 8.5},
          {"archetype": "triceps_extension", "sets": 10, "rpe": 9.0},
          {"archetype": "squat_lunge", "sets": 4, "rpe": 5.5}
        ]
      }
    }
  }'
```

### Trap 5 — Concurrent AMPK–mTOR, Glycogen & 48h Hinge Recovery (`interference_tax`)
- **Literature:** Wilson et al. (2012, `DOI: 10.1519/JSC.0b013e31823a3e2d`), Robineau et al. (2016, `DOI: 10.1519/JSC.0000000000000798`), Schumann et al. (2022, `DOI: 10.1007/s40279-021-01587-7`), Seiler (2010, `DOI: 10.1123/ijspp.5.3.276`).

```bash
curl -sS https://struggl.singandclap.com/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "interference_tax",
      "arguments": {
        "sessions": [
          {"start": "2026-11-10T07:00:00", "type": "endurance", "duration_min": 95, "intensity": "moderate", "modality": "run", "distance_km": 16.0},
          {"start": "2026-11-10T09:00:00", "type": "strength", "duration_min": 60, "intensity": "heavy", "lower_body": true, "hinge": true},
          {"start": "2026-11-11T07:00:00", "type": "endurance", "duration_min": 50, "intensity": "hard", "modality": "run", "distance_km": 10.0}
        ]
      }
    }
  }'
```
