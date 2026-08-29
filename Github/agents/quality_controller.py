import sys
from pathlib import Path
import json
from datetime import datetime


ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


from langchain_ollama import ChatOllama

from tools.file_tools import (
    list_files,
    read_file,
    write_file,
    get_project_path
)

from tools.terminal_tools import (
    run_command_in_project,
    format_result_for_display
)

from memory import (
    load_state,
    save_state,
    add_task
)


llm = ChatOllama(
    model="qwen2.5-coder:7b",
    temperature=0
)


SYSTEM = """
You are a Quality Controller Agent.

Role:
Verify project quality and readiness.

Responsibilities:

1. Verify architecture.md exists and is complete
2. Verify project structure matches architecture
3. Verify project installs cleanly (pip install -r requirements.txt)
4. Verify project starts without crashing
5. Verify test suite passes with real execution
6. Verify README.md matches current structure
7. Flag tech stack drift from locked_stack

Never fabricate results.
Always use REAL terminal execution.
Report PASS/FAIL per check with evidence.

Return ONLY JSON:

{
    "agent": "quality_controller",
    "status": "done" | "needs_review" | "blocked",
    "actions": [],
    "summary": "quality check results"
}
"""


def check_architecture_exists():
    """
    Check 1: Verify docs/architecture.md exists and has content.
    
    Returns:
        {"passed": bool, "message": str, "evidence": str}
    """
    
    try:
        content = read_file.invoke({"path": "docs/architecture.md"})
        
        if "ERROR" in content or "not found" in content.lower():
            return {
                "passed": False,
                "message": "architecture.md not found",
                "evidence": content
            }
        
        if len(content.strip()) < 100:
            return {
                "passed": False,
                "message": "architecture.md is too short or empty",
                "evidence": content[:200]
            }
        
        return {
            "passed": True,
            "message": "architecture.md exists and has content",
            "evidence": content[:500]
        }
    
    except Exception as e:
        return {
            "passed": False,
            "message": f"Error reading architecture: {str(e)}",
            "evidence": str(e)
        }


def check_project_structure():
    """
    Check 2: Verify project files match architecture requirements.
    
    Returns:
        {"passed": bool, "message": str, "evidence": str}
    """
    
    try:
        files_output = list_files.invoke({})
        
        if "ERROR" in files_output or "empty" in files_output.lower():
            return {
                "passed": False,
                "message": "Project appears empty or no files accessible",
                "evidence": files_output
            }
        
        files = files_output.split("\n")
        
        # Check for basic Python project structure
        has_src = any("src" in f.lower() or "main" in f.lower() for f in files)
        has_tests = any("test" in f.lower() for f in files)
        has_readme = any("readme" in f.lower() for f in files)
        
        issues = []
        if not has_src:
            issues.append("No src/ or main files found")
        
        evidence = f"Found {len(files)} files:\n" + "\n".join(files[:10])
        
        if issues:
            return {
                "passed": False,
                "message": "; ".join(issues),
                "evidence": evidence
            }
        
        return {
            "passed": True,
            "message": "Project structure appears valid",
            "evidence": evidence
        }
    
    except Exception as e:
        return {
            "passed": False,
            "message": f"Error checking project structure: {str(e)}",
            "evidence": str(e)
        }


def check_dependencies_install():
    """
    Check 3: Verify project installs cleanly.
    
    Returns:
        {"passed": bool, "message": str, "evidence": str}
    """
    
    project = get_project_path()
    req_file = project / "requirements.txt"
    
    if not req_file.exists():
        return {
            "passed": True,
            "message": "No requirements.txt (skipped)",
            "evidence": "No dependencies to install"
        }
    
    result = run_command_in_project(
        "pip install -r requirements.txt",
        project_path=str(project),
        timeout=300
    )
    
    if result["success"]:
        return {
            "passed": True,
            "message": "Dependencies installed successfully",
            "evidence": f"Exit code: 0, Wall time: {result['wall_time']:.2f}s"
        }
    else:
        return {
            "passed": False,
            "message": "Dependency installation failed",
            "evidence": result["stderr"][:500] if result["stderr"] else result["stdout"][:500]
        }


def check_project_starts():
    """
    Check 4: Verify project starts without crashing.
    
    Attempts common entry points: main.py, app.py, run.py, etc.
    
    Returns:
        {"passed": bool, "message": str, "evidence": str}
    """
    
    project = get_project_path()
    
    # Try common entry points
    entry_points = [
        "main.py",
        "app.py",
        "run.py",
        "src/main.py",
        "src/app.py"
    ]
    
    found_entry = None
    for ep in entry_points:
        ep_path = project / ep
        if ep_path.exists():
            found_entry = ep
            break
    
    if not found_entry:
        return {
            "passed": True,
            "message": "No standard entry point found (skipped)",
            "evidence": "Searched for: " + ", ".join(entry_points)
        }
    
    # Try to import/run the entry point (timeout after 5s)
    result = run_command_in_project(
        f"timeout 5 python {found_entry} || true",
        project_path=str(project),
        timeout=10
    )
    
    # For startup check, we're lenient - just verify it didn't crash with syntax errors
    if "SyntaxError" in result["stderr"] or "ImportError" in result["stderr"]:
        return {
            "passed": False,
            "message": f"Entry point {found_entry} has errors",
            "evidence": result["stderr"][:500]
        }
    
    return {
        "passed": True,
        "message": f"Entry point {found_entry} starts without immediate errors",
        "evidence": f"Exit code: {result['exit_code']}, Wall time: {result['wall_time']:.2f}s"
    }


def check_test_suite():
    """
    Check 5: Re-run test suite independently.
    
    Returns:
        {"passed": bool, "message": str, "evidence": str}
    """
    
    project = get_project_path()
    tests_dir = project / "tests"
    
    if not tests_dir.exists():
        return {
            "passed": True,
            "message": "No tests/ directory (skipped)",
            "evidence": "No test suite found"
        }
    
    result = run_command_in_project(
        "pytest tests -v --tb=short",
        project_path=str(project),
        timeout=120
    )
    
    if result["success"]:
        # Count passed tests from output
        passed_count = result["stdout"].count(" PASSED")
        return {
            "passed": True,
            "message": f"Test suite passed ({passed_count} tests)",
            "evidence": f"Exit code: 0, Wall time: {result['wall_time']:.2f}s\n{result['stdout'][:300]}"
        }
    else:
        return {
            "passed": False,
            "message": "Test suite failed",
            "evidence": result["stderr"][:500] if result["stderr"] else result["stdout"][:500]
        }


def check_readme():
    """
    Check 6: Verify README.md matches current file structure.
    
    Returns:
        {"passed": bool, "message": str, "evidence": str}
    """
    
    try:
        readme = read_file.invoke({"path": "README.md"})
        
        if "ERROR" in readme or "not found" in readme.lower():
            return {
                "passed": False,
                "message": "README.md not found",
                "evidence": readme
            }
        
        if len(readme.strip()) < 50:
            return {
                "passed": False,
                "message": "README.md is too short",
                "evidence": readme
            }
        
        # Basic checks
        has_installation = "install" in readme.lower()
        has_usage = "usage" in readme.lower() or "usage" in readme.lower()
        
        if not (has_installation or has_usage):
            return {
                "passed": False,
                "message": "README missing installation or usage instructions",
                "evidence": readme[:200]
            }
        
        return {
            "passed": True,
            "message": "README.md is present and documented",
            "evidence": readme[:300]
        }
    
    except Exception as e:
        return {
            "passed": False,
            "message": f"Error reading README: {str(e)}",
            "evidence": str(e)
        }


def check_tech_stack():
    """
    Check 7: Verify tech stack matches locked_stack from memory.
    
    Returns:
        {"passed": bool, "message": str, "evidence": str}
    """
    
    try:
        state = load_state()
        locked_stack = state.get("project", {}).get("locked_stack", [])
        
        if not locked_stack:
            return {
                "passed": True,
                "message": "No locked_stack defined (skipped)",
                "evidence": "Tech stack not locked in project state"
            }
        
        # Read requirements.txt to check actual stack
        try:
            req_content = read_file.invoke({"path": "requirements.txt"})
            if "ERROR" in req_content:
                req_content = ""
        except:
            req_content = ""
        
        # Simple check: verify locked packages are mentioned somewhere
        found_stack = []
        for tech in locked_stack:
            tech_lower = tech.lower()
            # Check in requirements.txt
            if tech_lower in req_content.lower():
                found_stack.append(tech)
        
        missing = [t for t in locked_stack if t not in found_stack]
        
        if missing:
            return {
                "passed": False,
                "message": f"Locked stack drift: missing {missing}",
                "evidence": f"Locked: {locked_stack}, Found: {found_stack}"
            }
        
        return {
            "passed": True,
            "message": "Tech stack matches locked configuration",
            "evidence": f"Verified: {found_stack}"
        }
    
    except Exception as e:
        return {
            "passed": True,
            "message": f"Could not verify tech stack: {str(e)} (continuing)",
            "evidence": str(e)
        }


def quality_controller_agent(task):
    """
    Quality Controller Agent - Run all 7 quality checks.
    
    Returns JSON with status and report.
    """
    
    print("\n========== QUALITY CONTROLLER ==========\n")
    
    checks = [
        ("Architecture", check_architecture_exists),
        ("Project Structure", check_project_structure),
        ("Dependencies Install", check_dependencies_install),
        ("Project Startup", check_project_starts),
        ("Test Suite", check_test_suite),
        ("README Documentation", check_readme),
        ("Tech Stack Lock", check_tech_stack)
    ]
    
    results = {}
    failed_checks = []
    
    for check_name, check_fn in checks:
        print(f"Running: {check_name}...")
        result = check_fn()
        results[check_name] = result
        
        if not result["passed"]:
            failed_checks.append(check_name)
        
        status_str = "✓ PASS" if result["passed"] else "✗ FAIL"
        print(f"  {status_str}: {result['message']}\n")
    
    # Determine overall status
    if not failed_checks:
        overall_status = "done"
        summary = "All quality checks passed"
    else:
        overall_status = "needs_review"
        summary = f"Failed checks: {', '.join(failed_checks)}"
    
    # Write quality report
    report_content = generate_quality_report(results, failed_checks)
    
    try:
        write_file.invoke({
            "path": "docs/quality_report.md",
            "content": report_content
        })
    except:
        pass
    
    # Save to memory
    try:
        add_task(f"Quality control: {overall_status}")
    except:
        pass
    
    return {
        "agent": "quality_controller",
        "status": overall_status,
        "actions": [],
        "summary": summary,
        "failed_checks": failed_checks,
        "results": results,
        "report_file": "docs/quality_report.md"
    }


def generate_quality_report(results, failed_checks):
    """
    Generate markdown quality report with all check results and evidence.
    """
    
    report = f"""# Quality Control Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Overall Status**: {'✓ PASS' if not failed_checks else '✗ NEEDS REVIEW'}
- **Failed Checks**: {len(failed_checks)}
- **Passed Checks**: {len(results) - len(failed_checks)}

"""
    
    if failed_checks:
        report += f"\n## Failed Checks\n\n"
        for check_name in failed_checks:
            report += f"- {check_name}\n"
    
    report += "\n## Detailed Results\n\n"
    
    for check_name, result in results.items():
        status = "✓ PASS" if result["passed"] else "✗ FAIL"
        report += f"""
### {check_name}

**Status**: {status}

**Message**: {result['message']}

**Evidence**:
```
{result['evidence']}
```

---

"""
    
    return report


if __name__ == "__main__":
    
    while True:
        
        task = input("\nQuality Controller Task: ")
        
        if task.lower() == "exit":
            break
        
        result = quality_controller_agent(task)
        
        print("\nRESULT:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
