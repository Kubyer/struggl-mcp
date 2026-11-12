# Cline One-Click Installation Guide — STRUGGL Hybrid Coach (`struggl-mcp`)

Install the STRUGGL Streamable HTTP MCP server in Cline with zero local Python setup.

## Option A — Instant Zero-Auth Setup (All 7 Free Sports-Science Calculators)

Add the `"struggl"` entry below to your `cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "struggl": {
      "type": "streamableHttp",
      "url": "https://struggl.singandclap.com/mcp",
      "disabled": false,
      "autoApprove": [
        "hyrox_pace",
        "hyrox_splits",
        "hyrox_autopsy",
        "strength_benchmark",
        "plates_zone2",
        "volume_audit",
        "interference_tax"
      ]
    }
  }
}
```

## Option B — Personal Athlete Ledger Sync (Optional)

To read your real training sessions, 17-muscle weekly MEV/MAV/MRV volume, and log or schedule workouts:

1. Ask the user to visit `https://struggl.singandclap.com/connect` (1st month of Coach is free, no credit card) and click **Generate Agent Token** to obtain a `stg_ath_...` token.
2. Add the `"headers"` block to the `"struggl"` server entry in `cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "struggl": {
      "type": "streamableHttp",
      "url": "https://struggl.singandclap.com/mcp",
      "headers": {
        "Authorization": "Bearer stg_ath_REPLACE_WITH_PERSONAL_TOKEN"
      },
      "disabled": false,
      "autoApprove": [
        "hyrox_pace",
        "hyrox_splits",
        "hyrox_autopsy",
        "strength_benchmark",
        "plates_zone2",
        "volume_audit",
        "interference_tax",
        "get_profile",
        "get_sessions",
        "get_muscle_volume"
      ]
    }
  }
}
```
