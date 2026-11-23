<p align="center">
  <img src="assets/logo.svg" width="88" height="88" alt="STRUGGL Logo" />
</p>

<h1 align="center">struggl-mcp — Zero-LLM-Math Sports Science MCP &amp; Agent Skill</h1>

<p align="center">
  <strong>Stop letting LLMs guess your 1RM, Zone 2 heart rate, weekly muscle volume, and Hyrox splits.</strong><br/>
  7 free unauthenticated sports-science calculators + optional stateful hybrid-athlete training ledger for Claude Code, Google Antigravity, Cursor, OpenAI Codex, Grok, Cline, and OpenClaw.
</p>

<p align="center">
  <a href="https://struggl.singandclap.com/connect">Connect &amp; Docs</a> ·
  <a href="benchmarks/llm_fitness_math_traps.md">5 LLM Exercise Math Traps</a> ·
  <a href="skills/struggl-coach/SKILL.md">Agent Skill (<code>SKILL.md</code>)</a> ·
  <a href="https://struggl.singandclap.com/science">Living Science Equations</a>
</p>

<p align="center">
  <a href="https://www.claudeai.directory/launches/struggl" target="_blank" rel="noopener"><img src="https://www.claudeai.directory/badge/struggl?theme=dark" alt="STRUGGL - Listed on Claude AI Directory" width="220" height="54" /></a>
</p>

<p align="center">
  <a href="https://glama.ai/mcp/servers/Kubyer/struggl-mcp"><img src="https://glama.ai/mcp/servers/Kubyer/struggl-mcp/badges/score.svg" alt="Kubyer/struggl-mcp MCP server" /></a>
</p>

---

## Why This Exists

Ask a frontier LLM what belt weight an `80 kg` athlete (`+30 kg x 5 @ RPE 9` pull-up) should use for `8 reps @ RPE 8`, and it routinely forgets the `80 kg` bodyweight on the bar — overshooting the belt prescription by **+5 kg**. Ask for Zone 2 heart rate (`35` yo, `48 bpm` RHR) and it defaults to `220 - Age`, under-prescribing by **19 bpm**. Ask if `10` sets of triceps isolation on top of `26` pressing sets is recoverable, and it misses **+13 fractional synergist sets** above MRV.

Full reproducible breakdown with `curl` calls and PubMed/Crossref DOIs: **[`benchmarks/llm_fitness_math_traps.md`](benchmarks/llm_fitness_math_traps.md)**.

`struggl-mcp` gives any coding or personal AI agent **13 deterministic tools** over stateless Streamable HTTP (`https://struggl.singandclap.com/mcp`) + an interactive **MCP Apps UI Card** (`ui://struggl/coach-card.html`) + a portable **`agentskills.io` `SKILL.md`**.

---

## 7 Free Science Tools (Zero Auth, Zero Install, Instant Value)

Connect `https://struggl.singandclap.com/mcp` with **no token and no signup** to unlock all 7 deterministic calculators immediately:

| Tool | What It Computes | Literature / Model Basis |
|---|---|---|
| `hyrox_pace` | Compromised Hyrox pace band, `8x1 km` run total, race time & Riegel 10K/HM/Marathon | 200k-finisher curve + Riegel (1981) |
| `hyrox_splits` | Exact Lap 1–8 `1 km` splits (`0.94x`–`1.03x`), Pro/Doubles offsets & Lap 1 overpacing blow-up cost | 200k-finisher piecewise decay (`DOI: 10.3389/fphys.2025.1519240`) |
| `hyrox_autopsy` | Post-race or mock-sim diagnostic: per-lap fade vs. target + P25–P75 station bottleneck leaks | Empirical station variance benchmarks |
| `strength_benchmark` | Piecewise Wathan e1RM, sex/BW/age score (`0–100`), tier (`untrained` -> `elite`) & kg to next tier | Wathan (1994) / LeSuer et al. (1997) |
| `plates_zone2` | `reps @ RPE` working weight (with BW system load on `pull_up`/`chin_up`/`dip`), gym plate pairs & Zone 2 bpm | Zourdos (2016) RIR + Tanaka (2001) & Karvonen (1957) HRR |
| `volume_audit` | Weekly 17-muscle hypertrophy audit (`1.0x` prime / `0.5x` synergist, `RPE >= 6` hard-set gate) & junk volume | Schoenfeld (2017), Pelland (2024), Robinson (2024) |
| `interference_tax` | Weekly hybrid schedule conflict check (`<3h`/`3–6h` AMPK-mTOR, `36h` glycogen, `48h` hinge, `80/20` drift) | Wilson (2012), Robineau (2016), Schumann (2022), Seiler (2010) |

---

## 6 Personal Training Ledger Tools (Optional Account Sync)

For athletes who want their coding agent to fetch a 1-call physiological coaching brief (`get_coaching_brief`), check real 14-day fatigue between coding blocks, audit live weekly sets, and batch-log or schedule workouts (`get_profile`, `get_sessions`, `get_muscle_volume`, `log_workout`, `plan_workout` — automatically mirrored into a read-only feed in the STRUGGL mobile/web app):

1. Start your **30-day free STRUGGL Coach trial (no credit card)** at **[https://struggl.singandclap.com/connect](https://struggl.singandclap.com/connect)**.
2. Connect via **OAuth 2.1 + PKCE** (`https://struggl.singandclap.com/v1/connector/mcp`) or generate a scoped `read` / `read + write` personal token (`stg_ath_...`).

---

## 10-Second Install Across Every Agent Platform

### 1. Claude Code &amp; Claude Desktop / Web

**1-Click OAuth 2.1 Sign-In (Recommended — Zero Manual API Keys):**
```bash
claude mcp add --transport http struggl https://struggl.singandclap.com/v1/connector/mcp
```
*(In Claude Code run `/mcp` → `struggl` → **Authenticate**; in Claude.ai / ChatGPT Connectors paste `https://struggl.singandclap.com/v1/connector/mcp` to open browser sign-in + interactive `ui://struggl/coach-card.html` UI cards.)*

**Instant Zero-Auth (7 free science calculators + Agent Skill):**
```bash
claude mcp add --transport http struggl https://struggl.singandclap.com/mcp
```
Or install the full plugin + skills via Claude Code's plugin manager:
```text
/plugin marketplace add Kubyer/struggl-mcp
/plugin install struggl@struggl-marketplace
```

**Headless Personal Token Fallback:**
```bash
claude mcp add --transport http struggl https://struggl.singandclap.com/mcp \
  --header "Authorization: Bearer stg_ath_YOUR_PERSONAL_TOKEN"
```

### 2. Universal `SKILL.md` (`skills.sh` — Cursor, Antigravity, Claude Code, Codex, Copilot)
```bash
npx skills add Kubyer/struggl-mcp
```

### 3. Google Antigravity
Install directly via `plugin.json` (OAuth 2.1 automatic sign-in on `https://struggl.singandclap.com/v1/connector/mcp`), or add to `~/.gemini/antigravity/mcp_config.json`:
```json
{
  "mcpServers": {
    "struggl": {
      "serverUrl": "https://struggl.singandclap.com/mcp"
    }
  }
}
```

### 4. Cursor & Windsurf (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "struggl": {
      "url": "https://struggl.singandclap.com/mcp"
    }
  }
}
```

### 5. OpenAI Codex &amp; ChatGPT (`~/.codex/config.toml` / Custom MCP)
```toml
[mcp_servers.struggl]
url = "https://struggl.singandclap.com/mcp"
```
*(In ChatGPT Connectors, connect `https://struggl.singandclap.com/v1/connector/mcp` via OAuth 2.1.)*

### 6. Gemini CLI (`geminicli.com/extensions`)
```bash
gemini extensions install https://github.com/Kubyer/struggl-mcp
```

### 7. Lovable (`lovable.dev`)
In your Lovable workspace (`Settings → Connectors → Custom MCP Server`), add `https://struggl.singandclap.com/mcp` for zero-auth sports-science tools while building fitness apps, or `https://struggl.singandclap.com/v1/connector/mcp` with OAuth 2.1.

### 8. OpenClaw / ClawHub &amp; Nous Hermes
```bash
clawhub install struggl-coach
```

### 9. One-Line CLI / Local `stdio` Bridge (`npx`, `uvx`, Python)

For local `stdio`-only MCP hosts without native Streamable HTTP support:

```bash
# Node.js >= 18 (zero-dependency npx stdio bridge -> https://struggl.singandclap.com/mcp)
npx -y struggl-mcp

# Python >= 3.10 (also installs `import struggl_primitives`)
uvx struggl-mcp
# or: pip install struggl-mcp && struggl-mcp
```

Set `STRUGGL_API_TOKEN=stg_ath_YOUR_PERSONAL_TOKEN` in the MCP server's `env` if you also want the 6 personal ledger tools alongside the 7 zero-auth science calculators.

---

## Open-Core Primitives for Fitness &amp; Coaching AI Builders

Building your own strength, running, Hyrox, or wearable coaching agent? Never let raw LLM prose improvise exercise math:

- **[`struggl_primitives.py`](struggl_primitives.py):** Pure-stdlib Python reference functions (`wathan_e1rm`, `prescribe_working_load`, `karvonen_zone2`, `ewma_acwr`, `hyrox_compromised_pace`, `fractional_set_credit`) plus ready-to-register `PRIMITIVE_TOOL_SCHEMAS`.
- **[`skills/fitness-agent-primitives/SKILL.md`](skills/fitness-agent-primitives/SKILL.md):** Builder skill teaching coding agents where stateless single-session math ends and longitudinal 30-day state (implicit RIR envelopes, `0.82^d / 0.96^d` EWMA ACWR, 17-muscle weekly MEV/MAV/MRV, 48h concurrent interference gating) begins.

---

## Repository Architecture &amp; Open-Source Standards

This repository follows the multi-registry agent package layout so a single repo works cleanly across MCP registries and Agent Skill directories:

```text
struggl-mcp/
├── server.json                         # Official MCP Registry schema (2025-12-11)
├── plugin.json / mcp_config.json       # Google Antigravity, Cursor & Grok Bot manifest
├── .claude-plugin/                     # Claude Code plugin & marketplace manifests
├── .mcp.json                           # Root Streamable HTTP MCP config (zero auth ready)
├── agents/openai.yaml                  # OpenAI Codex / Dots skill-to-MCP wiring
├── llms-install.md                     # Cline Marketplace 1-click installer
├── struggl_primitives.py               # Pure-stdlib stateless exercise-physiology primitives
├── skills/
│   ├── struggl-coach/                  # Athlete coaching skill + inline UI card template
│   └── fitness-agent-primitives/       # Builder skill for custom fitness & Hyrox AI agents
├── benchmarks/llm_fitness_math_traps.md
├── bin/cli.mjs                         # Zero-dependency npx stdio-to-HTTP bridge
├── package.json / pyproject.toml       # npm (`npx struggl-mcp`) & PyPI (`uvx struggl-mcp`) manifests
└── mcp_server.py                       # Zero-secret thin HTTP->stdio client (httpx + mcp only)
```

## Security &amp; Privacy

- **Zero Secrets in Repo:** This repository contains declarative manifests, open-source skill instructions, pure-stdlib physiology primitives, literature benchmarks, and a thin HTTP client (`mcp_server.py` imports only Python stdlib, `httpx`, `pydantic`, and `mcp`). Run `python scripts/verify_public_bundle.py` to audit every file.
- **OAuth 2.1 + Scoped Revocable Tokens:** Supports 1-click OAuth 2.1 + PKCE (`https://struggl.singandclap.com/v1/connector/mcp`) and optional scoped tokens (`stg_ath_...`), stored server-side strictly as SHA-256 hashes and revocable at `https://struggl.singandclap.com/connect`.
- **Privacy Policy, Terms &amp; Support:** [Privacy Policy](https://struggl.singandclap.com/privacy) · [Terms of Service](https://struggl.singandclap.com/terms) · [API &amp; Connector Docs](https://struggl.singandclap.com/v1/connector/docs) · `taha@tbaziz.com`.

## License

Apache License 2.0 — see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE). Covers the manifests, `SKILL.md` workflows, `struggl_primitives.py` reference primitives, benchmark documentation, and thin `mcp_server.py` client in this repository. The hosted STRUGGL coaching engine and longitudinal datasets at `struggl.singandclap.com` are operated by Sing And Clap.
