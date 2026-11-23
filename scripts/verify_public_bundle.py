#!/usr/bin/env python3
"""
Zero-Secret, IP-Isolation & Open-Source Registry Validator for `struggl-mcp`.

Validates:
  1. Zero secrets, tokens, private repo URLs, Supabase hosts, or internal emails.
  2. Zero proprietary backend imports (`mcp_server.py` imports ONLY stdlib + `httpx` + `mcp`).
  3. Compliance with all open-source Agent Skills & MCP Registry manifests:
     - Official MCP Registry `server.json` (description <= 100 chars, valid streamable-http remote)
     - Google Antigravity / Cursor / Grok `plugin.json` + `mcp_config.json` (3 suggestedPrompts, square logos)
     - Claude Code `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` + root `.mcp.json`
     - `agentskills.io` `skills/struggl-coach/SKILL.md` (name matches dir, description <= 1024 chars, < 500 lines)
     - OpenAI Codex `agents/openai.yaml` & Cline `llms-install.md`
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import List, Tuple

FORBIDDEN_FILE_PATTERNS = (
    re.compile(r"^\.env(\..+)?$"),
    re.compile(r".*credentials.*\.json$", re.IGNORECASE),
    re.compile(r".*\.(pem|key|p12|pfx)$", re.IGNORECASE),
)

# Built dynamically where needed so this file itself passes self-scan cleanly!
FORBIDDEN_CONTENT_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    ("OpenAI/Anthropic secret key", re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}")),
    ("Stripe key", re.compile(r"\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}")),
    ("Stripe webhook secret", re.compile(r"\bwhsec_[A-Za-z0-9]{16,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}")),
    ("PostHog API key", re.compile(r"\bph[cx]_[A-Za-z0-9]{20,}")),
    ("JWT token", re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}")),
    ("PEM private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Real STRUGGL athlete token", re.compile(r"\bstg_ath_[a-f0-9]{24,}\b")),
    ("STRUGGL B2B secret key", re.compile(r"\bstg_b2b_[A-Za-z0-9_-]{8,}")),
    ("Supabase project URL", re.compile(r"[a-z0-9-]+\.supabase\.co\b", re.IGNORECASE)),
    ("Private monorepo slug", re.compile(r"struggling" + r"_tbz")),
    ("Operator personal email", re.compile(r"tahabaziz" + r"@", re.IGNORECASE)),
    ("Backend env secret name", re.compile(r"\b(?:SUPABASE_SERVICE_ROLE_KEY|GOOGLE_CREDENTIALS_JSON|ANTHROPIC_API_KEY|GEMINI_API_KEY)\b")),
]

ALLOWED_MCP_SERVER_IMPORTS = frozenset({
    "__future__",
    "os",
    "sys",
    "typing",
    "httpx",
    "mcp",
    "pydantic",
})


def _parse_frontmatter(md_text: str) -> Tuple[dict, str]:
    if not md_text.startswith("---\n"):
        raise ValueError("SKILL.md must begin with YAML frontmatter `---`")
    end = md_text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("SKILL.md missing closing YAML frontmatter `---`")
    raw_yaml = md_text[4:end]
    body = md_text[end + 5:]
    parsed: dict = {}
    current_map: dict | None = None
    for line in raw_yaml.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.startswith("  ") and current_map is not None and ":" in line:
            k, v = line.strip().split(":", 1)
            current_map[k.strip()] = v.strip().strip('"').strip("'")
        elif ":" in line:
            k, v = line.split(":", 1)
            key = k.strip()
            val = v.strip()
            if not val:
                current_map = {}
                parsed[key] = current_map
            else:
                current_map = None
                parsed[key] = val.strip('"').strip("'")
    return parsed, body


def verify_bundle(bundle_root: Path) -> List[str]:
    errors: List[str] = []
    if not bundle_root.is_dir():
        return [f"Bundle directory does not exist: {bundle_root}"]

    # 1. Required multi-registry files
    required_paths = [
        "LICENSE",
        "NOTICE",
        "README.md",
        ".gitignore",
        "server.json",
        "plugin.json",
        ".cursor-plugin/plugin.json",
        "gemini-extension.json",
        ".agents/plugins/marketplace.json",
        "plugins/struggl-openai/plugin.json",
        "plugins/struggl-openai/mcp.json",
        "plugins/struggl-openai/skills/get-started/SKILL.md",
        "mcp_config.json",
        ".mcp.json",
        ".claude-plugin/marketplace.json",
        "plugins/struggl/.claude-plugin/plugin.json",
        "plugins/struggl/.mcp.json",
        "plugins/struggl/README.md",
        "plugins/struggl/LICENSE",
        "plugins/struggl/NOTICE",
        "agents/openai.yaml",
        "llms-install.md",
        "pyproject.toml",
        "package.json",
        "bin/cli.mjs",
        ".github/workflows/publish.yml",
        "requirements.txt",
        "mcp_server.py",
        "struggl_primitives.py",
        "benchmarks/llm_fitness_math_traps.md",
        "skills/struggl-coach/SKILL.md",
        "skills/struggl-coach/references/card_template.html",
        "skills/struggl-coach/references/science_tools_schema.md",
        "skills/fitness-agent-primitives/SKILL.md",
    ]
    for rel in required_paths:
        if not (bundle_root / rel).exists():
            errors.append(f"Missing required file: {rel}")
    if len(list((bundle_root / "assets").glob("*"))) < 4:
        errors.append("assets/ must contain SVG + square PNG logos")

    # 2. Scan every file in bundle for forbidden filenames & secret patterns
    self_path = (bundle_root / "scripts" / "verify_public_bundle.py").resolve()
    for p in sorted(bundle_root.rglob("*")):
        if "__pycache__" in p.parts or ".git" in p.parts:
            continue
        if p.is_dir():
            continue
        rel_str = str(p.relative_to(bundle_root))
        for pat in FORBIDDEN_FILE_PATTERNS:
            if pat.match(p.name):
                errors.append(f"Forbidden secret-like filename in bundle: {rel_str}")
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".ico"}:
            # Check PNG magic header
            if p.suffix.lower() == ".png" and p.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
                errors.append(f"Invalid PNG header: {rel_str}")
            continue
        text = p.read_text(encoding="utf-8")
        if p.resolve() != self_path:
            for label, regex in FORBIDDEN_CONTENT_PATTERNS:
                m = regex.search(text)
                if m:
                    errors.append(f"Forbidden pattern ({label}) in {rel_str}: {m.group(0)[:40]!r}")

    # 3. Verify `mcp_server.py` imports ONLY stdlib + httpx + mcp (zero backend coupling)
    mcp_py = bundle_root / "mcp_server.py"
    if mcp_py.exists():
        tree = ast.parse(mcp_py.read_text(encoding="utf-8"), filename="mcp_server.py")
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top not in ALLOWED_MCP_SERVER_IMPORTS:
                        errors.append(f"Disallowed import in mcp_server.py: {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                top = node.module.split(".")[0]
                if top not in ALLOWED_MCP_SERVER_IMPORTS:
                    errors.append(f"Disallowed from-import in mcp_server.py: {node.module}")

    # 4. Validate Official MCP Registry `server.json`
    server_path = bundle_root / "server.json"
    if server_path.exists():
        sj = json.loads(server_path.read_text(encoding="utf-8"))
        if sj.get("name") != "io.github.Kubyer/struggl":
            errors.append(f"Unexpected server.json name: {sj.get('name')!r}")
        desc = sj.get("description", "")
        if not (1 <= len(desc) <= 100):
            errors.append(f"server.json description must be 1..100 chars for mcp-publisher (got {len(desc)})")
        remotes = sj.get("remotes") or []
        if not remotes or remotes[0].get("type") != "streamable-http" or remotes[0].get("url") != "https://struggl.singandclap.com/mcp":
            errors.append("server.json remotes[0] must target streamable-http https://struggl.singandclap.com/mcp")

    # 5. Validate Antigravity / Cursor `plugin.json` & Claude `.claude-plugin/`
    plugin_path = bundle_root / "plugin.json"
    if plugin_path.exists():
        pj = json.loads(plugin_path.read_text(encoding="utf-8"))
        if pj.get("name") != "struggl":
            errors.append("plugin.json name must be lowercase 'struggl'")
        if len(pj.get("suggestedPrompts") or []) != 3:
            errors.append("plugin.json must have exactly 3 suggestedPrompts")
        logo_rel = pj.get("logo", "")
        if not logo_rel or logo_rel.startswith("/") or ".." in logo_rel or not (bundle_root / logo_rel).exists():
            errors.append(f"plugin.json logo path invalid or missing: {logo_rel!r}")

    cursor_plugin_path = bundle_root / ".cursor-plugin" / "plugin.json"
    if cursor_plugin_path.exists():
        cur_pj = json.loads(cursor_plugin_path.read_text(encoding="utf-8"))
        if cur_pj.get("name") != "struggl":
            errors.append(".cursor-plugin/plugin.json name must be 'struggl'")

    gemini_ext_path = bundle_root / "gemini-extension.json"
    if gemini_ext_path.exists():
        gem_ext = json.loads(gemini_ext_path.read_text(encoding="utf-8"))
        if gem_ext.get("name") != "struggl" or "struggl" not in (gem_ext.get("mcpServers") or {}):
            errors.append("gemini-extension.json must define name='struggl' and mcpServers.struggl")

    # 5c. Validate PyPI & npm package manifests (`pyproject.toml`, `package.json`, `bin/cli.mjs`)
    pyproject_path = bundle_root / "pyproject.toml"
    pkg_json_path = bundle_root / "package.json"
    cli_mjs_path = bundle_root / "bin" / "cli.mjs"
    if pyproject_path.exists() and pkg_json_path.exists():
        py_ver_match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject_path.read_text(encoding="utf-8"), re.MULTILINE)
        py_ver = py_ver_match.group(1) if py_ver_match else ""
        pkg = json.loads(pkg_json_path.read_text(encoding="utf-8"))
        if pkg.get("name") != "struggl-mcp":
            errors.append(f"package.json name must be 'struggl-mcp' (got {pkg.get('name')!r})")
        if not py_ver or pkg.get("version") != py_ver:
            errors.append(f"package.json version ({pkg.get('version')!r}) must match pyproject.toml ({py_ver!r})")
        if (pkg.get("bin") or {}).get("struggl-mcp") != "./bin/cli.mjs":
            errors.append("package.json bin['struggl-mcp'] must point to './bin/cli.mjs'")
        if pkg.get("dependencies"):
            errors.append("package.json must stay zero-dependency (dependencies must be omitted or empty)")
        repo_url = (pkg.get("repository") or {}).get("url")
        if repo_url != "git+https://github.com/Kubyer/struggl-mcp.git":
            errors.append(f"package.json repository.url must match Kubyer/struggl-mcp for npm OIDC, got {repo_url!r}")
        if cli_mjs_path.exists():
            cli_txt = cli_mjs_path.read_text(encoding="utf-8")
            if not cli_txt.startswith("#!/usr/bin/env node\n"):
                errors.append("bin/cli.mjs must start with '#!/usr/bin/env node'")
            if f'VERSION = "{py_ver}"' not in cli_txt:
                errors.append(f"bin/cli.mjs VERSION must match pyproject.toml ({py_ver!r})")

    # 5a. Validate OpenAI ChatGPT & Codex Universal Plugin (`plugins/struggl-openai/` + `.agents/plugins/marketplace.json`)
    oa_mkt_path = bundle_root / ".agents" / "plugins" / "marketplace.json"
    if oa_mkt_path.exists():
        oa_mkt = json.loads(oa_mkt_path.read_text(encoding="utf-8"))
        oa_plugins = oa_mkt.get("plugins") or []
        if not oa_plugins or oa_plugins[0].get("name") != "struggl":
            errors.append(".agents/plugins/marketplace.json must declare plugin 'struggl'")

    oa_bundle = bundle_root / "plugins" / "struggl-openai"
    if oa_bundle.is_dir():
        oapj = json.loads((oa_bundle / "plugin.json").read_text(encoding="utf-8"))
        if oapj.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
            errors.append("plugins/struggl-openai/plugin.json missing Agent Plugins 1.0.0 $schema")
        oa_ext = ((oapj.get("extensions") or {}).get("com.openai") or {})
        oa_iface = oa_ext.get("interface") or {}
        if len(oa_iface.get("displayName") or "") > 30:
            errors.append("OpenAI interface.displayName must be <= 30 chars")
        if len(oa_iface.get("shortDescription") or "") > 30:
            errors.append("OpenAI interface.shortDescription must be <= 30 chars")
        for url_key in ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
            if not str(oa_iface.get(url_key) or "").startswith("https://"):
                errors.append(f"OpenAI interface.{url_key} must be https://")
        for p_str in oa_iface.get("defaultPrompt") or []:
            if len(p_str) > 128 or "@" in p_str:
                errors.append(f"OpenAI defaultPrompt invalid (>128 chars or contains @): {p_str!r}")
        for icon_key in ("composerIcon", "composerIconDark", "logo", "logoDark"):
            rel_icon = oa_iface.get(icon_key) or ""
            if not rel_icon.startswith("./") or not (oa_bundle / rel_icon[2:]).exists():
                errors.append(f"OpenAI {icon_key} missing or not ./-prefixed: {rel_icon!r}")
        oa_review = ((oa_ext.get("review") or {}).get("test_cases") or {})
        if len(oa_review.get("positive") or []) != 5 or len(oa_review.get("negative") or []) != 3:
            errors.append("OpenAI review.test_cases requires 5 positive and 3 negative cases")
        oamcp = json.loads((oa_bundle / "mcp.json").read_text(encoding="utf-8"))
        if ((oamcp.get("mcpServers") or {}).get("struggl") or {}).get("url") != "https://struggl.singandclap.com/v1/connector/mcp":
            errors.append("plugins/struggl-openai/mcp.json must target https://struggl.singandclap.com/v1/connector/mcp")

    claude_dir = bundle_root / ".claude-plugin"
    if claude_dir.is_dir():
        allowed_claude_files = {"marketplace.json"}
        actual_claude_files = {f.name for f in claude_dir.iterdir()}
        extra = actual_claude_files - allowed_claude_files
        if extra:
            errors.append(f".claude-plugin/ at root must only contain marketplace.json, found: {sorted(extra)}")
        for cf in allowed_claude_files:
            if (claude_dir / cf).exists():
                json.loads((claude_dir / cf).read_text(encoding="utf-8"))

    # 5b. Validate dedicated Claude Directory bundle (`plugins/struggl/`)
    claude_bundle = bundle_root / "plugins" / "struggl"
    if claude_bundle.is_dir():
        cpj_path = claude_bundle / ".claude-plugin" / "plugin.json"
        if cpj_path.exists():
            cpj = json.loads(cpj_path.read_text(encoding="utf-8"))
            for req_key in ("privacyPolicyUrl", "supportUrl", "documentationUrl", "termsOfServiceUrl", "icon"):
                if not cpj.get(req_key):
                    errors.append(f"plugins/struggl/.claude-plugin/plugin.json missing {req_key}")
        cmcp_path = claude_bundle / ".mcp.json"
        if cmcp_path.exists():
            cmcp = json.loads(cmcp_path.read_text(encoding="utf-8"))
            url = ((cmcp.get("mcpServers") or {}).get("struggl") or {}).get("url")
            if url != "https://struggl.singandclap.com/v1/connector/mcp":
                errors.append(f"plugins/struggl/.mcp.json must match Connector URL, got {url!r}")
        allowed_ext = {".md", ".json", ".png"}
        for fp in sorted(claude_bundle.rglob("*")):
            if fp.is_dir():
                continue
            if fp.name not in {"LICENSE", "NOTICE"} and fp.suffix.lower() not in allowed_ext:
                errors.append(f"Disallowed file type in plugins/struggl/: {fp.relative_to(claude_bundle)}")
            if fp.suffix.lower() in {".md", ".json"} or fp.name in {"LICENSE", "NOTICE"}:
                txt = fp.read_text(encoding="utf-8")
                if "../" in txt or "..\\" in txt:
                    errors.append(f"Relative parent climb in {fp.relative_to(claude_bundle)}")
                if re.search(r"\b(?:STRUGGL_API_TOKEN|stg_ath_|curl\s+-|npx\s+|uvx\s+)", txt):
                    errors.append(f"Disallowed token/launcher pattern in {fp.relative_to(claude_bundle)}")

    # 6. Validate `skills/*/SKILL.md` (`agentskills.io` spec) + pure-stdlib `struggl_primitives.py`
    prim_py = bundle_root / "struggl_primitives.py"
    if prim_py.exists():
        allowed_prim_imports = frozenset({"__future__", "math", "typing"})
        ptree = ast.parse(prim_py.read_text(encoding="utf-8"), filename="struggl_primitives.py")
        for node in ast.walk(ptree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] not in allowed_prim_imports:
                        errors.append(f"Disallowed import in struggl_primitives.py: {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.split(".")[0] not in allowed_prim_imports:
                    errors.append(f"Disallowed from-import in struggl_primitives.py: {node.module}")

    for skill_name in ("struggl-coach", "fitness-agent-primitives"):
        skill_path = bundle_root / "skills" / skill_name / "SKILL.md"
        if skill_path.exists():
            raw_skill = skill_path.read_text(encoding="utf-8")
            fm, body = _parse_frontmatter(raw_skill)
            if fm.get("name") != skill_name:
                errors.append(f"SKILL.md frontmatter name must match folder {skill_name!r} (got {fm.get('name')!r})")
            s_desc = fm.get("description", "")
            if not (20 <= len(s_desc) <= 1024):
                errors.append(f"{skill_name}/SKILL.md description must be 20..1024 chars (got {len(s_desc)})")
            line_count = len(raw_skill.splitlines())
            if line_count > 500:
                errors.append(f"{skill_name}/SKILL.md must stay <= 500 lines (got {line_count})")
            if len(body.split()) > 3500:
                errors.append(f"{skill_name}/SKILL.md body exceeds recommended token budget")

    return errors


def main() -> int:
    default_root = Path(__file__).resolve().parent.parent
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else default_root
    errs = verify_bundle(target)
    if errs:
        print(f"FAILED public bundle verification ({len(errs)} error(s)):")
        for e in errs:
            print(f"  - {e}")
        return 1
    print(f"OK: {target} passed zero-secret, zero-backend-import, and multi-registry manifest checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
