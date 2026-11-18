#!/usr/bin/env node
/**
 * Thin zero-dependency MCP stdio-to-HTTP bridge for STRUGGL (`npx -y struggl-mcp`).
 *
 * Forwards newline-delimited JSON-RPC 2.0 frames from stdin to
 * `${STRUGGL_API_URL || "https://struggl.singandclap.com"}/mcp` (Streamable HTTP)
 * and preserves the server's `Mcp-Session-Id` header across calls.
 *
 * - All 7 sports-science calculators work with zero authentication.
 * - Set `STRUGGL_API_TOKEN=stg_ath_...` to unlock personal ledger sync tools.
 */
import { createInterface } from "node:readline";

const VERSION = "1.4.0";
const DEFAULT_API_URL = "https://struggl.singandclap.com";
const TIMEOUT_MS = 30_000;

const args = process.argv.slice(2);
if (args.includes("-v") || args.includes("--version")) {
  process.stdout.write(`${VERSION}\n`);
  process.exit(0);
}
if (args.includes("-h") || args.includes("--help")) {
  process.stdout.write(
    [
      `struggl-mcp v${VERSION} — Thin stdio MCP bridge to STRUGGL (${DEFAULT_API_URL}/mcp)`,
      "",
      "Usage:",
      "  npx -y struggl-mcp",
      "  STRUGGL_API_TOKEN=stg_ath_... npx -y struggl-mcp",
      "",
      "Environment variables:",
      "  STRUGGL_API_TOKEN   Optional personal Bearer token from https://struggl.singandclap.com/connect",
      `  STRUGGL_API_URL     Optional base URL override (default: ${DEFAULT_API_URL})`,
      "",
    ].join("\n"),
  );
  process.exit(0);
}

const apiBase = (process.env.STRUGGL_API_URL || DEFAULT_API_URL).replace(/\/+$/, "");
const endpoint = `${apiBase}/mcp`;
const token = (process.env.STRUGGL_API_TOKEN || "").trim();

let sessionId = null;

function writeMessage(msg) {
  process.stdout.write(`${JSON.stringify(msg)}\n`);
}

function makeRpcError(id, code, message) {
  return { jsonrpc: "2.0", id, error: { code, message } };
}

function emitErrorForPayload(payload, code, message) {
  if (Array.isArray(payload)) {
    const errors = payload
      .filter((item) => item && item.id !== undefined && item.id !== null)
      .map((item) => makeRpcError(item.id, code, message));
    if (errors.length > 0) writeMessage(errors);
    return;
  }
  const id = payload?.id;
  if (id !== undefined && id !== null) {
    writeMessage(makeRpcError(id, code, message));
  }
}

function parseSsePayloads(body) {
  const messages = [];
  for (const rawLine of body.split(/\r?\n/)) {
    if (!rawLine.startsWith("data:")) continue;
    const data = rawLine.slice(5).trim();
    if (!data || data === "[DONE]") continue;
    messages.push(JSON.parse(data));
  }
  return messages;
}

async function forwardLine(rawLine) {
  const trimmed = rawLine.trim();
  if (!trimmed) return;

  let payload;
  try {
    payload = JSON.parse(trimmed);
  } catch (err) {
    const detail = err instanceof Error ? err.message : String(err);
    writeMessage(makeRpcError(null, -32700, `Invalid JSON: ${detail}`));
    return;
  }

  const headers = {
    "Content-Type": "application/json",
    Accept: "application/json, text/event-stream",
    "User-Agent": `struggl-mcp-npx/${VERSION}`,
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (sessionId) headers["Mcp-Session-Id"] = sessionId;

  let res;
  try {
    res = await fetch(endpoint, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
  } catch (err) {
    const detail = err instanceof Error ? err.message : String(err);
    emitErrorForPayload(payload, -32000, `Could not reach Struggl MCP: ${detail}`);
    return;
  }

  const nextSid = res.headers.get("mcp-session-id");
  if (nextSid) sessionId = nextSid;

  if (res.status === 202 || res.status === 204) return;

  const text = await res.text();
  if (!res.ok) {
    const snippet = text ? ` — ${text.slice(0, 300)}` : "";
    emitErrorForPayload(payload, -32000, `Struggl MCP returned HTTP ${res.status}${snippet}`);
    return;
  }
  if (!text.trim()) return;

  const contentType = (res.headers.get("content-type") || "").toLowerCase();
  try {
    if (contentType.includes("text/event-stream")) {
      for (const msg of parseSsePayloads(text)) {
        writeMessage(msg);
      }
      return;
    }
    writeMessage(JSON.parse(text));
  } catch (err) {
    const detail = err instanceof Error ? err.message : String(err);
    emitErrorForPayload(payload, -32603, `Invalid MCP response payload: ${detail}`);
  }
}

const rl = createInterface({ input: process.stdin, crlfDelay: Infinity });
let chain = Promise.resolve();

rl.on("line", (line) => {
  chain = chain.then(() => forwardLine(line)).catch((err) => {
    const detail = err instanceof Error ? err.stack || err.message : String(err);
    process.stderr.write(`struggl-mcp bridge error: ${detail}\n`);
  });
});

rl.on("close", () => {
  chain.finally(() => process.exit(0));
});
