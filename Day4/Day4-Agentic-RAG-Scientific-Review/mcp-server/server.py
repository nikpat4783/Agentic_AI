"""MCP server exposing reusable dev-workflow tools for this project.

Run standalone: python server.py (stdio transport, for use as an MCP server
entry in a client's .mcp.json / `claude mcp add`).

All paths are resolved relative to this file's location, not the caller's
cwd, so this server works regardless of where it's launched from.
"""
import importlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
from pathlib import Path

from mcp.server.mcpserver import MCPServer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
OBSERVABILITY_DIR = PROJECT_ROOT / "observability"
LOADTEST_DIR = PROJECT_ROOT / "loadtest"
DOMAINS_CONFIG_PATH = BACKEND_DIR / "app" / "domains" / "config.py"
TOOL_SCHEMAS_PATH = BACKEND_DIR / "app" / "agent" / "tools" / "schemas.py"
TOOLS_DIR = BACKEND_DIR / "app" / "agent" / "tools"
PID_FILE = PROJECT_ROOT / ".dev-pids.json"
LOG_DIR = PROJECT_ROOT / ".dev-logs"

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
    """Start the backend (uvicorn on :8001) and frontend (vite on :5173) dev servers in the background if not already running. Returns their URLs, PIDs, and log file paths."""
    LOG_DIR.mkdir(exist_ok=True)
    pids = _load_pids()
    lines = []

    venv_python = BACKEND_DIR / ".venv" / "bin" / "python"
    if pids.get("backend") and _pid_alive(pids["backend"]):
        lines.append(f"backend already running (pid {pids['backend']}, http://localhost:8001)")
    elif not venv_python.exists():
        lines.append("backend NOT started: backend/.venv not found -- run `make install` first.")
    else:
        log = open(LOG_DIR / "backend.log", "w")
        proc = subprocess.Popen(
            [str(venv_python), "-m", "uvicorn", "app.main:app", "--port", "8001"],
            cwd=BACKEND_DIR, stdout=log, stderr=log, start_new_session=True,
        )
        pids["backend"] = proc.pid
        lines.append(f"backend started (pid {proc.pid}, http://localhost:8001, log: {LOG_DIR / 'backend.log'})")

    if pids.get("frontend") and _pid_alive(pids["frontend"]):
        lines.append(f"frontend already running (pid {pids['frontend']}, http://localhost:5173)")
    elif not (FRONTEND_DIR / "node_modules").exists():
        lines.append("frontend NOT started: node_modules not found -- run `make install` first.")
    else:
        log = open(LOG_DIR / "frontend.log", "w")
        proc = subprocess.Popen(
            ["npm", "run", "dev", "--", "--port", "5173"],
            cwd=FRONTEND_DIR, stdout=log, stderr=log, start_new_session=True,
        )
        pids["frontend"] = proc.pid
        lines.append(f"frontend started (pid {proc.pid}, http://localhost:5173, log: {LOG_DIR / 'frontend.log'})")

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
    via `docker compose up -d` in observability/. Idempotent -- safe to call if already running."""
    if not OBSERVABILITY_DIR.exists():
        return "observability/ directory not found."
    code, output = _run(["docker", "compose", "up", "-d"], cwd=OBSERVABILITY_DIR, timeout=120)
    status = "started" if code == 0 else f"FAILED (exit {code})"
    return f"Observability stack: {status}\n\n{_tail(output)}\n\nGrafana: http://localhost:3000"


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
    """Run a k6 load-test scenario against the backend, pushing metrics into the
    observability stack's Prometheus (visualize at http://localhost:3000/d/k6-load-test).

    scenario: "smoke" (default; safe, no external API calls) or "agentic_rag"
    (opt-in, makes real billed Groq calls -- requires GROQ_API_KEY
    to already be set in this process's environment; this tool does not accept
    or forward a key as an argument, so it can't be logged/echoed by a caller).
    """
    if scenario not in ("smoke", "agentic_rag"):
        return f"Error: unknown scenario '{scenario}'. Use 'smoke' or 'agentic_rag'."
    k6_bin = LOADTEST_DIR / "bin" / "k6"
    if not k6_bin.exists():
        return "k6 not installed -- run loadtest/install-k6.sh first."
    script = LOADTEST_DIR / "scripts" / f"{scenario}.js"
    if scenario == "agentic_rag" and not os.environ.get("GROQ_API_KEY"):
        return "Error: GROQ_API_KEY is not set in this process's environment -- refusing to run the cost-incurring scenario."
    env = {
        **os.environ,
        "K6_PROMETHEUS_RW_SERVER_URL": "http://localhost:9090/api/v1/write",
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


def _import_domain_registry():
    sys.path.insert(0, str(BACKEND_DIR))
    if "app.domains.config" in sys.modules:
        module = importlib.reload(sys.modules["app.domains.config"])
    else:
        module = importlib.import_module("app.domains.config")
    return module.DOMAIN_REGISTRY


@mcp.tool()
def list_domains() -> str:
    """List the app's current research domains (id, name, description) read live from backend/app/domains/config.py."""
    registry = _import_domain_registry()
    if not registry:
        return "No domains registered."
    return "\n".join(f"- {d.id}: {d.name} -- {d.description}" for d in registry.values())


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


@mcp.tool()
def add_domain(
    domain_id: str,
    name: str,
    description: str,
    system_prompt_suffix: str,
    example_question_1: str,
    example_question_2: str = "",
) -> str:
    """Add a new research domain to backend/app/domains/config.py's DOMAIN_REGISTRY.

    domain_id must be a unique lowercase snake_case identifier (e.g. "genomics").
    Fails with a clear error instead of touching the file if domain_id is
    malformed or already exists. The running backend must be restarted to
    pick up the change.
    """
    if not re.fullmatch(r"[a-z][a-z0-9_]*", domain_id):
        return f"Error: domain_id '{domain_id}' must be lowercase snake_case (e.g. 'genomics')."

    registry = _import_domain_registry()
    if domain_id in registry:
        return f"Error: domain '{domain_id}' already exists."

    questions = [q for q in (example_question_1, example_question_2) if q]
    if not questions:
        return "Error: example_question_1 is required."

    source = DOMAINS_CONFIG_PATH.read_text()
    marker = "}\n\n\ndef get_domain"
    if marker not in source:
        return (
            "Error: could not find the expected DOMAIN_REGISTRY closing marker "
            "in config.py -- refusing to edit. Add the domain manually."
        )

    questions_literal = ", ".join(f'"{_escape(q)}"' for q in questions)
    entry = (
        f'    "{_escape(domain_id)}": DomainConfig(\n'
        f'        id="{_escape(domain_id)}",\n'
        f'        name="{_escape(name)}",\n'
        f'        description="{_escape(description)}",\n'
        f'        system_prompt_suffix=(\n'
        f'            "{_escape(system_prompt_suffix)}"\n'
        f'        ),\n'
        f'        example_questions=[{questions_literal}],\n'
        f'    ),\n'
    )
    new_source = source.replace(marker, f"{entry}}}\n\n\ndef get_domain", 1)
    DOMAINS_CONFIG_PATH.write_text(new_source)
    return f"Added domain '{domain_id}' to config.py. Restart the backend to pick it up."


@mcp.tool()
def scaffold_new_tool(tool_name: str, description: str) -> str:
    """Scaffold a new agent tool: creates backend/app/agent/tools/<tool_name>_tool.py
    with a stub matching this repo's existing tool conventions (async function,
    never raises -- returns {"error": ...} on failure), and appends a matching
    entry to TOOL_SCHEMAS in schemas.py.

    This only creates the skeleton. It does NOT wire the tool into the agent
    orchestrator's dispatch table or write a test -- those steps require
    tool-specific judgment and are left as documented follow-ups (see
    .claude/skills/dev-workflow/SKILL.md, "Adding a new agent tool").
    """
    if not re.fullmatch(r"[a-z][a-z0-9_]*", tool_name):
        return f"Error: tool_name '{tool_name}' must be lowercase snake_case (e.g. 'search_clinicaltrials')."

    tool_file = TOOLS_DIR / f"{tool_name}_tool.py"
    if tool_file.exists():
        return f"Error: {tool_file.relative_to(PROJECT_ROOT)} already exists."

    schemas_source = TOOL_SCHEMAS_PATH.read_text()
    if f'"name": "{tool_name}"' in schemas_source:
        return f"Error: a tool named '{tool_name}' already has a schema entry in schemas.py."

    stripped = schemas_source.rstrip()
    if not stripped.endswith("]"):
        return "Error: schemas.py doesn't end with the expected TOOL_SCHEMAS closing ']' -- refusing to edit."

    schema_entry = (
        "    {\n"
        '        "type": "function",\n'
        '        "function": {\n'
        f'            "name": "{tool_name}",\n'
        f'            "description": "{_escape(description)}",\n'
        '            "parameters": {\n'
        '                "type": "object",\n'
        '                "properties": {\n'
        '                    "query": {"type": "string", "description": "Search query."},\n'
        '                },\n'
        '                "required": ["query"],\n'
        "            },\n"
        "        },\n"
        "    },\n"
    )
    # stripped[:-1] drops only the trailing "]", leaving the previous entry's
    # own trailing "," and newline intact -- don't add another comma here.
    new_schemas_source = stripped[:-1] + schema_entry + "]\n"
    TOOL_SCHEMAS_PATH.write_text(new_schemas_source)

    tool_stub = (
        f'async def {tool_name}(query: str, max_results: int = 5) -> dict:\n'
        f'    """TODO: implement {tool_name} ({description}).\n\n'
        f'    Must never raise -- catch everything and return {{"error": "..."}}\n'
        f'    so the agent orchestrator loop stays alive on failure.\n'
        f'    """\n'
        f'    try:\n'
        f'        # TODO: implement the actual lookup/action here.\n'
        f'        return {{"results": []}}\n'
        f'    except Exception as exc:\n'
        f'        return {{"error": f"{tool_name} failed: {{exc}}"}}\n'
    )
    tool_file.write_text(tool_stub)

    return (
        f"Created {tool_file.relative_to(PROJECT_ROOT)} and added its schema to "
        f"schemas.py. Remaining manual steps: implement the TODO in the new "
        f"file, dispatch it in orchestrator.py's _dispatch_tool, and add a test "
        f"in backend/tests/test_{tool_name}_tool.py."
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
