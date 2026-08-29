import sys
from pathlib import Path
import json
import re
from datetime import datetime


ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


from agents.planner import create_plan


from agents.architect import architect_agent
from agents.developer import developer_agent
from agents.tester import tester_agent
from agents.reviewer import reviewer_agent
from agents.security import security_agent
from agents.debug import debug_agent
from agents.refactor import refactor_agent
from agents.documentation import documentation_agent
from agents.git_manager import git_manager_agent
from agents.quality_controller import quality_controller_agent


from tools.file_tools import (
    create_project,
    set_active_project,
    write_file as write_file_tool
)


from tools.terminal_tools import (
    run_command_in_project,
    format_result_for_display
)

from memory import (
    set_memory_project,
    update_project,
    load_state,
    save_state,
    write_agent_memory,
    read_agent_memory,
    save_state_json
)

from agents import output_validator


# ==============================
# Agent Registry
# ==============================

AGENTS = {

    "architect": architect_agent,

    "developer": developer_agent,

    "tester": tester_agent,

    "reviewer": reviewer_agent,

    "security": security_agent,

    "debug": debug_agent,

    "refactor": refactor_agent,

    "documentation": documentation_agent,

    "git_manager": git_manager_agent,

    "quality_controller": quality_controller_agent

}


# Enforced workflow order (FIX7)
ENFORCED_WORKFLOW = [
    "architect",
    "developer",
    "tester",
    "reviewer",
    "security",
    "debug",
    "refactor",
    "documentation",
    "git_manager",
    "quality_controller"
]

MAX_QUALITY_RETRIES = 3


# Simple locked stack extractor (FIX5)
TECH_KEYWORDS = [
    "python", "flask", "django", "fastapi", "uvicorn", "gunicorn",
    "postgres", "postgresql", "sqlite", "mysql", "docker", "redis",
    "celery", "react", "vue", "node", "express", "typescript",
    "pytest", "sqlalchemy", "pydantic", "aiohttp", "gunicorn"
]


def extract_locked_stack(text: str):
    text_lower = (text or "").lower()
    found = []
    for kw in TECH_KEYWORDS:
        if kw in text_lower and kw not in found:
            found.append(kw)
    return found


# Mapping from quality check to agent stages to rerun (used by FIX7 targeted retry)
CHECK_TO_AGENTS = {
    "Architecture": ["architect"],
    "Project Structure": ["architect", "developer"],
    "Dependencies Install": ["tester"],
    "Project Startup": ["developer"],
    "Test Suite": ["tester"],
    "README Documentation": ["documentation"],
    "Tech Stack Lock": ["architect", "developer"]
}


# Agent call + validation wrapper (FIX1)
RETRY_MESSAGE = (
    "Your last output put a JSON action inside the file content field. The content field must be the raw final file content only. Retry."
)


def call_agent_with_validation(agent_fn, agent_name, task, project_name):
    """
    Call agent and validate its output using agents/output_validator.
    If write_file content looks like a JSON action object, retry once with the exact retry message.
    Returns a dict: {"valid":bool, "parsed":dict_or_none, "errors":[], "attempts":n}
    """
    attempts = 0
    last_parsed = None
    errors = []

    while attempts < 2:
        attempts += 1
        # provide locked_stack in task context (agents should honor it)
        try:
            raw = agent_fn(task)
        except Exception as e:
            return {"valid": False, "parsed": None, "errors": [f"Agent raised exception: {e}"], "attempts": attempts}

        # normalize strings
        parsed = None
        if isinstance(raw, str):
            txt = raw.strip().replace("```json", "").replace("```", "").strip()
            try:
                parsed = json.loads(txt)
            except Exception:
                parsed = None
        elif isinstance(raw, dict):
            parsed = raw

        if parsed is None:
            # can't validate structured output; return as invalid
            errors.append("Could not parse agent output as JSON/dict")
            # do not retry if unparsable
            return {"valid": False, "parsed": None, "errors": errors, "attempts": attempts}

        # Validate structure
        v = output_validator.validate_agent_output(parsed)
        if v["valid"]:
            return {"valid": True, "parsed": parsed, "errors": [], "attempts": attempts}

        # If validation errors include JSON action in file content, retry once with exact message
        content_errors = [e for e in v["errors"] if "content appears to be JSON action object" in e]
        if content_errors and attempts == 1:
            # append retry message to task context and retry
            task = task + "\n\n" + RETRY_MESSAGE
            continue

        # Other errors or second failure -> return invalid
        return {"valid": False, "parsed": parsed, "errors": v["errors"], "attempts": attempts}

    return {"valid": False, "parsed": last_parsed, "errors": errors, "attempts": attempts}


# Execute actions produced by agent and persist to per-agent memory (FIX2, FIX6)

def execute_actions(actions, project_name, agent_name):
    executed = []
    for i, action in enumerate(actions):
        typ = action.get("type")
        if typ == "write_file":
            path = action.get("path")
            content = action.get("content", "")
            # defensive check already enforced by validation in manager; file_tools also guards
            res = write_file_tool.invoke({"path": path, "content": content})
            executed.append({"action_index": i, "type": "write_file", "path": path, "result": res})
        elif typ == "run_terminal":
            cmd = action.get("command")
            # run in project directory
            project_path = str(Path(project_name)) if project_name else None
            res = run_command_in_project(cmd, project_path=project_path, timeout=300)
            executed.append({"action_index": i, "type": "run_terminal", "command": cmd, "result": res})
        elif typ == "note":
            executed.append({"action_index": i, "type": "note", "message": action.get("message")})
        else:
            executed.append({"action_index": i, "type": "unknown", "raw": action})

    # Save executed actions to agent memory
    try:
        mem = read_agent_memory(project_name, agent_name)
        mem.setdefault("history", [])
        mem["history"].append({"time": str(datetime.utcnow()), "executed_actions": executed})
        write_agent_memory(project_name, agent_name, mem)
    except Exception:
        pass

    return executed


# Map planner plan to enforced workflow tasks (planner may only provide context)

def build_stage_tasks(plan, project_request):
    # plan is dict with 'plan' list of steps possibly containing agent and task
    tasks = {agent: None for agent in ENFORCED_WORKFLOW}
    if isinstance(plan, dict) and "plan" in plan and isinstance(plan["plan"], list):
        for step in plan["plan"]:
            a = step.get("agent")
            t = step.get("task")
            if a in tasks and not tasks[a]:
                tasks[a] = t
    # Default tasks if missing: use project_request
    for a in tasks:
        if not tasks[a]:
            tasks[a] = project_request
    return tasks


# Determine agents to rerun based on quality_controller failed checks (FIX7)

def map_failed_checks_to_agents(failed_checks):
    agents_to_run = []
    for chk in failed_checks:
        agents = CHECK_TO_AGENTS.get(chk, [])
        for a in agents:
            if a not in agents_to_run:
                agents_to_run.append(a)
    return agents_to_run


# Main workflow runner (enforces FIX7)

def run_workflow(project_request):
    print("\n========== PROJECT PLANNING ==========")

    plan = create_plan(project_request)

    # Planner must only provide context; validate plan partially but ignore ordering
    if not isinstance(plan, dict) or "plan" not in plan:
        print("Planner did not return a usable plan — proceeding with default tasks")

    # Create project
    project_name = plan.get("project_name") if isinstance(plan, dict) else None
    if not project_name:
        project_name = re.sub(r"[^a-zA-Z0-9_-]", "_", (plan.get("project_name") if isinstance(plan, dict) else None) or "new_project").lower()

    print("\nNEW PROJECT:", project_name)

    create_project.invoke({"name": project_name})
    set_active_project.invoke({"name": project_name})

    # Setup per-project memory
    set_memory_project(project_name)

    # Extract locked_stack from user request and persist
    locked_stack = extract_locked_stack(project_request)
    # Save into project state.json
    save_state_json(project_name, {"project": {"name": project_name, "locked_stack": locked_stack}})

    # Save plan/context into project memory
    update_project(project_name, project_request)

    # Build tasks per enforced workflow
    stage_tasks = build_stage_tasks(plan, project_request)

    print("\n========== PLAN ==========")
    print(json.dumps(stage_tasks, indent=2, ensure_ascii=False))

    results = []

    # Run each stage in enforced order
    for agent_name in ENFORCED_WORKFLOW:
        print(f"\n===============================\n\nRUNNING {agent_name.upper()}\n\n===============================\n")
        agent_fn = AGENTS.get(agent_name)
        task = stage_tasks.get(agent_name)
        # Prepend locked_stack info to task for agent enforcement (FIX5)
        if locked_stack:
            locked_block = "\n\nLocked stack (enforce): " + ", ".join(locked_stack)
            task_for_agent = str(task) + locked_block
        else:
            task_for_agent = str(task)

        if agent_fn is None:
            print(f"Agent {agent_name} not found")
            results.append({"agent": agent_name, "status": "NOT_FOUND"})
            continue

        # Call agent with validation
        call_res = call_agent_with_validation(agent_fn, agent_name, task_for_agent, project_name)
        if not call_res.get("valid"):
            # Stage failed — record and continue (do not execute writes)
            results.append({"agent": agent_name, "status": "FAILED", "reason": call_res.get("errors")})
            # Save to agent memory
            try:
                write_agent_memory(project_name, agent_name, {"history": [{"time": str(datetime.utcnow()), "status": "FAILED", "errors": call_res.get("errors")} ]})
            except Exception:
                pass
            continue

        parsed = call_res.get("parsed")
        actions = parsed.get("actions", []) if isinstance(parsed, dict) else []
        # Execute actions and save results into agent memory
        executed = execute_actions(actions, project_name, agent_name)

        results.append({"agent": agent_name, "status": "SUCCESS", "result": parsed, "executed": executed})

        # Save overall agent result to memory
        try:
            write_agent_memory(project_name, agent_name, {"history": [{"time": str(datetime.utcnow()), "status": "SUCCESS", "result": parsed}]})
        except Exception:
            pass

    # After initial pass, run quality_controller explicitly and handle targeted retries
    qc_attempt = 0
    qc_result = None
    while qc_attempt <= MAX_QUALITY_RETRIES:
        qc_attempt += 1
        print("\n========== RUNNING QUALITY_CONTROLLER ==========")
        # Run quality_controller with context
        qc_task = project_request
        if locked_stack:
            qc_task = qc_task + "\n\nLocked stack (enforce): " + ", ".join(locked_stack)
        qc_call = call_agent_with_validation(quality_controller_agent, "quality_controller", qc_task, project_name)
        if not qc_call.get("valid") and qc_call.get("parsed") is None:
            qc_result = {"status": "failed", "reason": qc_call.get("errors")}
            break
        qc_parsed = qc_call.get("parsed")
        # quality_controller_agent returns its own status and failed_checks
        if isinstance(qc_parsed, dict):
            qc_result = qc_parsed
        else:
            # If agent returned string/dict but not parsed structure, try direct call
            try:
                qc_result = quality_controller_agent(qc_task)
            except Exception as e:
                qc_result = {"status": "failed", "reason": str(e)}

        status = qc_result.get("status")
        if status == "done":
            print("Quality controller passed all checks")
            results.append({"agent": "quality_controller", "status": "done", "result": qc_result})
            break
        elif status == "needs_review":
            failed_checks = qc_result.get("failed_checks", [])
            agents_to_rerun = map_failed_checks_to_agents(failed_checks)
            # Only rerun stages that are earlier than quality_controller and in enforced order
            if not agents_to_rerun:
                # nothing to rerun
                break
            print(f"Quality controller requests rerun of: {agents_to_rerun}")
            # Run only the flagged agents in enforced order
            for a in ENFORCED_WORKFLOW:
                if a in agents_to_rerun:
                    print(f"Re-running stage: {a}")
                    agent_fn = AGENTS.get(a)
                    task = stage_tasks.get(a)
                    if locked_stack:
                        task_for_agent = str(task) + "\n\nLocked stack (enforce): " + ", ".join(locked_stack)
                    else:
                        task_for_agent = str(task)
                    call_res = call_agent_with_validation(agent_fn, a, task_for_agent, project_name)
                    if not call_res.get("valid"):
                        # failed again — record and continue
                        write_agent_memory(project_name, a, {"history": [{"time": str(datetime.utcnow()), "status": "FAILED", "errors": call_res.get("errors")} ]})
                        print(f"Stage {a} failed validation on rerun: {call_res.get('errors')}")
                        continue
                    parsed = call_res.get("parsed")
                    actions = parsed.get("actions", [])
                    execute_actions(actions, project_name, a)
                    write_agent_memory(project_name, a, {"history": [{"time": str(datetime.utcnow()), "status": "SUCCESS_RERUN", "result": parsed}]})
            # After reruns, loop to run quality_controller again
            if qc_attempt >= MAX_QUALITY_RETRIES:
                print("Maximum quality retry cycles reached")
                results.append({"agent": "quality_controller", "status": "failed", "result": qc_result})
                break
            else:
                continue
        else:
            # blocked or other statuses
            results.append({"agent": "quality_controller", "status": status, "result": qc_result})
            break

    # Finalize state
    state = load_state()
    state.setdefault("project", {})
    state["project"]["status"] = "completed" if qc_result and qc_result.get("status") == "done" else "needs_attention"
    save_state(state)

    return {
        "project": project_name,
        "status": state["project"]["status"],
        "results": results,
        "quality": qc_result
    }


if __name__ == "__main__":

    while True:
        request = input("\nProject Request: ")
        if request.lower() == "exit":
            break
        result = run_workflow(request)
        print("\nFINAL REPORT:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
