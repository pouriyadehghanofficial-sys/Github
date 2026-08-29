"""
Memory helpers and per-agent memory management with compatibility wrappers.
Provides per-agent memory files at memory/{project}/{agent}.json and preserves
backwards compatibility with existing agents/memory.py functions by proxying and
migrating old project_state.md when needed.
"""
from pathlib import Path
import json
import agents.memory as old_mem
from datetime import datetime

BASE = Path(__file__).resolve().parent


def ensure_project_memory(project_name: str) -> Path:
    p = BASE / project_name
    p.mkdir(parents=True, exist_ok=True)
    return p


def agent_memory_path(project_name: str, agent_name: str) -> Path:
    p = ensure_project_memory(project_name)
    return p / f"{agent_name}.json"


def read_agent_memory(project_name: str, agent_name: str):
    ap = agent_memory_path(project_name, agent_name)
    if not ap.exists():
        return {"history": []}
    try:
        return json.loads(ap.read_text(encoding="utf-8"))
    except Exception:
        return {"history": [ap.read_text(encoding="utf-8")]}


def write_agent_memory(project_name: str, agent_name: str, payload):
    ap = agent_memory_path(project_name, agent_name)
    ap.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return True


def save_state_json(project_name: str, state_dict):
    p = ensure_project_memory(project_name)
    (p / "state.json").write_text(json.dumps(state_dict, indent=2, ensure_ascii=False), encoding="utf-8")
    return True


def load_state_json(project_name: str):
    p = ensure_project_memory(project_name)
    s = p / "state.json"
    if not s.exists():
        return {}
    try:
        return json.loads(s.read_text(encoding="utf-8"))
    except Exception:
        return {}


def migrate_project_state_md(project_name: str):
    # If the old project_state.md exists in memory/, migrate its content into planner.json
    old = BASE / "project_state.md"
    if not old.exists():
        return False
    content = old.read_text(encoding="utf-8")
    # Save migration into planner memory
    m = read_agent_memory(project_name, "planner")
    m.setdefault("history", [])
    m["history"].append({"migrated_project_state_md": content, "migrated_at": str(datetime.utcnow())})
    write_agent_memory(project_name, "planner", m)
    return True

# =========================
# Backwards-compatible wrappers for existing agents.memory API
# These proxy to agents.memory but also maintain per-agent JSON storage when appropriate
# =========================

def set_memory_project(name):
    # Proxy to old module for directory setup
    old_mem.set_memory_project(name)
    ensure_project_memory(name)
    # Migrate old md if present
    migrate_project_state_md(name)


def get_active_project():
    return old_mem.get_active_project()


def load_state():
    # Prefer old_mem state file for backward compatibility but also store a copy in state.json
    state = old_mem.load_state()
    # Persist a copy into memory/{project}/state.json
    project = state.get("project", {}).get("name") or get_active_project()
    if project:
        save_state_json(project, state)
    return state


def save_state(state):
    # Save using old_mem to preserve behavior
    old_mem.save_state(state)
    project = state.get("project", {}).get("name") or get_active_project()
    if project:
        save_state_json(project, state)


def update_project(name, description=""):
    old_mem.update_project(name, description)
    # Also ensure the state.json exists
    state = old_mem.load_state()
    save_state_json(name, state)


def add_test(result):
    old_mem.add_test(result)
    project = get_active_project()
    # Append to tester per-agent memory
    mem = read_agent_memory(project, "tester")
    mem.setdefault("history", [])
    mem["history"].append({"time": str(datetime.utcnow()), "result": result})
    write_agent_memory(project, "tester", mem)


def add_issue(issue):
    old_mem.add_issue(issue)
    project = get_active_project()
    mem = read_agent_memory(project, "tester_issues")
    mem.setdefault("history", [])
    mem["history"].append({"time": str(datetime.utcnow()), "issue": issue})
    write_agent_memory(project, "tester_issues", mem)


def add_agent_result(agent, result):
    old_mem.add_agent_result(agent, result)
    project = get_active_project()
    mem = read_agent_memory(project, agent)
    mem.setdefault("history", [])
    mem["history"].append({"time": str(datetime.utcnow()), "result": result})
    write_agent_memory(project, agent, mem)

# Export older helper names
def save_architecture(content):
    old_mem.save_architecture(content)

def add_decision(decision):
    old_mem.add_decision(decision)

def add_file(path):
    old_mem.add_file(path)

def add_task(task):
    old_mem.add_task(task)

def add_change(change):
    old_mem.add_change(change)

def show_memory():
    return load_state()
