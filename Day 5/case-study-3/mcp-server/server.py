"""MCP server exposing reusable dev-workflow and registry-extension tools for
this project.

Run standalone: python server.py (stdio transport, for use as an MCP server
entry in a client's .mcp.json / `claude mcp add`).

All paths are resolved relative to this file's location, not the caller's
cwd, so this server works regardless of where it's launched from.
"""
import json
import os
import re
import shutil
import signal
import subprocess
import sys
from pathlib import Path

import httpx
from mcp.server.mcpserver import MCPServer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
OBSERVABILITY_DIR = PROJECT_ROOT / "observability"
LOADTEST_DIR = PROJECT_ROOT / "loadtest"
SEED_SPECS_PATH = BACKEND_DIR / "app" / "extraction" / "seed_specs.py"
RULE_EXTRACTORS_PATH = BACKEND_DIR / "app" / "extraction" / "rule_extractors.py"
RAG_SPECS_DIR = BACKEND_DIR / "app" / "rag" / "specs"
PID_FILE = PROJECT_ROOT / ".dev-pids.json"
LOG_DIR = PROJECT_ROOT / ".dev-logs"
BACKEND_URL = "http://localhost:8002"

mcp = MCPServer("app-dev-orchestrator")


def _run(cmd: list[str], cwd: Path, timeout: int = 180) -> tuple[int | None, str]:
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, (result.stdout + result.stderr).strip()
    except subprocess.TimeoutExpired:
        return None, f"Command timed out after {timeout}s: {' '.join(cmd)}"
    except FileNotFoundError as exc:
        return None, f"Command not found: {exc}"


def _tail(text: str, n: int = 30) -> str:
    return "\n".join(text.splitlines()[-n:])


@mcp.tool()
def run_backend_tests() -> str:
    """Run the backend pytest suite and return a pass/fail summary with the tail of its output."""
    venv_python = BACKEND_DIR / ".venv" / "bin" / "python"
    if not venv_python.exists():
        return "Backend venv not found at backend/.venv -- run `make install` first."
    code, output = _run([str(venv_python), "-m", "pytest", "-q"], cwd=BACKEND_DIR)
    status = "PASSED" if code == 0 else f"FAILED (exit {code})"
    return f"Backend tests: {status}\n\n{_tail(output)}"


@mcp.tool()
def run_frontend_build() -> str:
    """Run the frontend production build (npm run build) and return a summary. Cleans up the dist/ output afterward."""
    if not (FRONTEND_DIR / "node_modules").exists():
        return "Frontend dependencies not installed -- run `make install` first."
    code, output = _run(["npm", "run", "build"], cwd=FRONTEND_DIR)
    dist = FRONTEND_DIR / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    status = "SUCCEEDED" if code == 0 else f"FAILED (exit {code})"
    return f"Frontend build: {status}\n\n{_tail(output)}"


def _load_pids() -> dict:
    if PID_FILE.exists():
        try:
            return json.loads(PID_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


@mcp.tool()
def start_dev_servers() -> str:
    """Start the backend (uvicorn on :8002) and frontend (vite on :5174) dev servers in the background if not already running. Returns their URLs, PIDs, and log file paths."""
    LOG_DIR.mkdir(exist_ok=True)
    pids = _load_pids()
    lines = []

    venv_python = BACKEND_DIR / ".venv" / "bin" / "python"
    if pids.get("backend") and _pid_alive(pids["backend"]):
        lines.append(f"backend already running (pid {pids['backend']}, http://localhost:8002)")
    elif not venv_python.exists():
        lines.append("backend NOT started: backend/.venv not found -- run `make install` first.")
    else:
        log = open(LOG_DIR / "backend.log", "w")
        proc = subprocess.Popen(
            [str(venv_python), "-m", "uvicorn", "app.main:app", "--port", "8002"],
            cwd=BACKEND_DIR, stdout=log, stderr=log, start_new_session=True,
        )
        pids["backend"] = proc.pid
        lines.append(f"backend started (pid {proc.pid}, http://localhost:8002, log: {LOG_DIR / 'backend.log'})")

    if pids.get("frontend") and _pid_alive(pids["frontend"]):
        lines.append(f"frontend already running (pid {pids['frontend']}, http://localhost:5174)")
    elif not (FRONTEND_DIR / "node_modules").exists():
        lines.append("frontend NOT started: node_modules not found -- run `make install` first.")
    else:
        log = open(LOG_DIR / "frontend.log", "w")
        proc = subprocess.Popen(
            ["npm", "run", "dev", "--", "--port", "5174"],
            cwd=FRONTEND_DIR, stdout=log, stderr=log, start_new_session=True,
        )
        pids["frontend"] = proc.pid
        lines.append(f"frontend started (pid {proc.pid}, http://localhost:5174, log: {LOG_DIR / 'frontend.log'})")

    PID_FILE.write_text(json.dumps(pids))
    return "\n".join(lines)


@mcp.tool()
def stop_dev_servers() -> str:
    """Stop any backend/frontend dev servers previously started by start_dev_servers."""
    pids = _load_pids()
    if not pids:
        return "No dev servers are tracked as running."
    lines = []
    for name, pid in pids.items():
        if _pid_alive(pid):
            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
                lines.append(f"{name} (pid {pid}) stopped")
            except ProcessLookupError:
                lines.append(f"{name} (pid {pid}) already gone")
        else:
            lines.append(f"{name} (pid {pid}) already gone")
    PID_FILE.unlink(missing_ok=True)
    return "\n".join(lines)


@mcp.tool()
def start_observability_stack() -> str:
    """Start the local observability stack (otel-collector, prometheus, loki, tempo, grafana)
    via `docker compose up -d` in observability/. Idempotent -- safe to call if already running.
    Uses this project's own ports (Grafana :3010, Prometheus :9091) and its own Compose
    project name, so it coexists with a similarly-named stack from another project."""
    if not OBSERVABILITY_DIR.exists():
        return "observability/ directory not found."
    code, output = _run(["docker", "compose", "up", "-d"], cwd=OBSERVABILITY_DIR, timeout=120)
    status = "started" if code == 0 else f"FAILED (exit {code})"
    return f"Observability stack: {status}\n\n{_tail(output)}\n\nGrafana: http://localhost:3010"


@mcp.tool()
def stop_observability_stack() -> str:
    """Stop the local observability stack via `docker compose down` in observability/."""
    if not OBSERVABILITY_DIR.exists():
        return "observability/ directory not found."
    code, output = _run(["docker", "compose", "down"], cwd=OBSERVABILITY_DIR, timeout=60)
    status = "stopped" if code == 0 else f"FAILED (exit {code})"
    return f"Observability stack: {status}\n\n{_tail(output)}"


@mcp.tool()
def run_load_test(scenario: str = "smoke") -> str:
    """Run a k6 load-test scenario against the backend, pushing metrics into this
    project's own Prometheus (visualize at http://localhost:3010/d/k6-load-test).

    scenario: "smoke" (default; safe, no external calls) or "extraction"
    (drives real document ingestion + extraction; safe/free by default since
    the backend degrades LLM-backed fields to "llm_unavailable" without a
    key -- pass a key via the LLM_API_KEY env var on this process yourself
    if you want to exercise the real LLM path; this tool does not accept or
    forward a key as an argument, so it can't be logged/echoed by a caller).
    """
    if scenario not in ("smoke", "extraction"):
        return f"Error: unknown scenario '{scenario}'. Use 'smoke' or 'extraction'."
    k6_bin = LOADTEST_DIR / "bin" / "k6"
    if not k6_bin.exists():
        return "k6 not installed -- run loadtest/install-k6.sh first."
    script = LOADTEST_DIR / "scripts" / f"{scenario}.js"
    env = {
        **os.environ,
        "K6_PROMETHEUS_RW_SERVER_URL": "http://localhost:9091/api/v1/write",
        "K6_PROMETHEUS_RW_TREND_STATS": "p(95),p(99),avg",
    }
    testid = f"{scenario}-mcp"
    try:
        result = subprocess.run(
            [str(k6_bin), "run", "--out", "experimental-prometheus-rw", "--tag", f"testid={testid}", str(script)],
            cwd=LOADTEST_DIR, capture_output=True, text=True, timeout=300, env=env,
        )
        status = "PASSED" if result.returncode == 0 else f"FAILED (exit {result.returncode})"
        return f"k6 {scenario}: {status}\n\n{_tail(result.stdout + result.stderr, 40)}"
    except subprocess.TimeoutExpired:
        return f"k6 {scenario} timed out after 300s."


@mcp.tool()
def list_data_element_specs() -> str:
    """List registered data-element specs. Reads live from the running backend's
    GET /specs if it's up; otherwise falls back to reading
    backend/app/extraction/seed_specs.py directly."""
    try:
        resp = httpx.get(f"{BACKEND_URL}/specs", timeout=3.0)
        resp.raise_for_status()
        specs = resp.json()
        return "\n".join(
            f"- {s['element_name']} ({s['doc_type']}, strategy={s['strategy']}, "
            f"requires_llm={s['requires_llm']}, threshold={s['threshold']})"
            for s in specs
        ) or "No specs registered."
    except httpx.HTTPError:
        if not SEED_SPECS_PATH.exists():
            return "Backend not reachable and seed_specs.py not found."
        sys.path.insert(0, str(BACKEND_DIR))
        import importlib

        module = importlib.import_module("app.extraction.seed_specs")
        specs = module.SEED_SPECS
        return "(backend not running, reading seed_specs.py)\n" + "\n".join(
            f"- {s['element_name']} ({s['doc_type']}, strategy={s['strategy']}, "
            f"requires_llm={s['requires_llm']}, threshold={s['threshold']})"
            for s in specs
        )


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


@mcp.tool()
def add_data_element_spec(
    element_name: str,
    doc_type: str,
    strategy: str,
    requires_llm: bool,
    threshold: float,
    spec_text: str,
) -> str:
    """Register a new data-element spec: appends an entry to
    backend/app/extraction/seed_specs.py's SEED_SPECS list and writes the
    grounding spec text to backend/app/rag/specs/<element_name>.md (re-indexed
    by the RAG retriever on the next backend restart).

    element_name must be a unique lowercase snake_case identifier. strategy
    must be "rule" or "llm". Fails with a clear error instead of touching any
    file if element_name is malformed or already exists, or strategy is
    invalid. The running backend must be restarted to pick up the change.
    """
    if not re.fullmatch(r"[a-z][a-z0-9_]*", element_name):
        return f"Error: element_name '{element_name}' must be lowercase snake_case (e.g. 'lab_bnp')."
    if strategy not in ("rule", "llm"):
        return f"Error: strategy must be 'rule' or 'llm', got '{strategy}'."
    # requires_llm must agree with strategy: registry.py's "rule" branch never
    # looks at requires_llm at all, and its "llm" branch always resolves to
    # llm_unavailable when requires_llm is False -- either mismatch silently
    # makes this element permanently unresolvable with no error surfaced.
    if strategy == "llm" and not requires_llm:
        return "Error: strategy='llm' requires requires_llm=True (registry.py's llm branch refuses to call the LLM otherwise, so this element would always queue for QA with no explanation)."
    if strategy == "rule" and requires_llm:
        return "Error: strategy='rule' elements never invoke the LLM (registry.py's rule branch ignores requires_llm), so requires_llm=True here would be misleading -- pass False."
    if not SEED_SPECS_PATH.exists():
        return "Error: backend/app/extraction/seed_specs.py not found -- has the backend been scaffolded yet?"

    source = SEED_SPECS_PATH.read_text()
    if f'"element_name": "{element_name}"' in source:
        return f"Error: a spec named '{element_name}' already exists in seed_specs.py."

    marker = "]"
    if not source.rstrip().endswith(marker):
        return "Error: seed_specs.py doesn't end with the expected SEED_SPECS closing ']' -- refusing to edit."

    spec_text_path = f"app/rag/specs/{element_name}.md"
    entry = (
        "    {\n"
        f'        "element_name": "{_escape(element_name)}",\n'
        f'        "doc_type": "{_escape(doc_type)}",\n'
        f'        "strategy": "{strategy}",\n'
        f'        "requires_llm": {"True" if requires_llm else "False"},\n'
        f'        "threshold": {threshold},\n'
        f'        "spec_text_path": "{spec_text_path}",\n'
        "    },\n"
    )
    stripped = source.rstrip()
    new_source = stripped[:-1] + entry + "]\n"
    SEED_SPECS_PATH.write_text(new_source)

    RAG_SPECS_DIR.mkdir(parents=True, exist_ok=True)
    (RAG_SPECS_DIR / f"{element_name}.md").write_text(spec_text.rstrip() + "\n")

    return (
        f"Added spec '{element_name}' to seed_specs.py and wrote "
        f"{spec_text_path}. If strategy='rule', also add a matching function "
        f"to rule_extractors.py (see scaffold_new_extractor). Restart the "
        f"backend to pick up the change and re-index RAG."
    )


@mcp.tool()
def scaffold_new_extractor(element_name: str, description: str) -> str:
    """Scaffold a new rule-based extractor: appends a stub entry to
    backend/app/extraction/rule_extractors.py's RULE_EXTRACTORS dict, matching
    this repo's ACTUAL contract -- every rule extractor returns a dict
    {"value": str | None, "raw_confidence": float, "error": str | None},
    never a bare value, because registry.py's rule dispatch branch does
    `{**result, "extraction_method": "rule"}` on whatever the function
    returns. A function returning a plain string/None instead of this dict
    shape would make that dict-spread raise, defeating the "extractors never
    raise" guarantee -- so this scaffold must never emit that wrong shape.

    Only creates the skeleton regex function; you still need to fill in the
    actual pattern. Assumes a matching DataElementSpec with strategy="rule"
    already exists (see add_data_element_spec) -- this tool does not create
    the spec itself.
    """
    if not re.fullmatch(r"[a-z][a-z0-9_]*", element_name):
        return f"Error: element_name '{element_name}' must be lowercase snake_case (e.g. 'lab_bnp')."
    if not RULE_EXTRACTORS_PATH.exists():
        return "Error: backend/app/extraction/rule_extractors.py not found -- has the backend been scaffolded yet?"

    source = RULE_EXTRACTORS_PATH.read_text()
    func_name = f"extract_{element_name}"
    if func_name in source:
        return f"Error: a function named '{func_name}' already exists in rule_extractors.py."

    stub = (
        f'\n\ndef {func_name}(text: str) -> dict:\n'
        f'    """TODO: implement extraction for {element_name} ({_escape(description)}).\n\n'
        f'    Must never raise, and must always return this exact dict shape\n'
        f'    (matching every other function in this file) -- registry.py\'s\n'
        f'    rule dispatch does {{**result, "extraction_method": "rule"}} on\n'
        f'    whatever this returns, so returning a bare string/None instead\n'
        f'    of the dict below would raise there, breaking the "never\n'
        f'    raises" guarantee (SPEC.md KPI 2).\n'
        f'    """\n'
        f'    # TODO: replace with a real regex/pattern for this field.\n'
        f'    match = None  # e.g. re.search(r"...", text)\n'
        f'    if match is None:\n'
        f'        return {{"value": None, "raw_confidence": 0.0, "error": None}}\n'
        f'    return {{"value": match.group(0), "raw_confidence": 0.95, "error": None}}\n'
    )
    new_source = source.rstrip() + stub
    if f'"{element_name}"' not in new_source:
        new_source += (
            f'\n\n# TODO: register in RULE_EXTRACTORS: "{element_name}": {func_name},\n'
        )
    RULE_EXTRACTORS_PATH.write_text(new_source)

    return (
        f"Appended stub function {func_name}() to rule_extractors.py, returning the "
        f"same {{value, raw_confidence, error}} dict shape as every existing rule "
        f"extractor (never a bare value -- see this tool's own docstring for why). "
        f"Remaining manual steps: implement the TODO pattern, register it in "
        f"the RULE_EXTRACTORS dict, and add a test."
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
