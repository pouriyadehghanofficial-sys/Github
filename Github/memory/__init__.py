"""
Memory helpers and per-agent memory management.
Provides:
- ensure_project_memory
- read_agent_memory
- write_agent_memory
- save_state_json
- migrate_project_state_md
"""
from pathlib import Path
import json

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
    m["history"].append({"migrated_project_state_md": content})
    write_agent_memory(project_name, "planner", m)
    return True
