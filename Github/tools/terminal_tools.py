"""
Terminal execution tools for agent actions.
Provides real command execution with subprocess, capturing stdout/stderr/exit code.
"""

import subprocess
import time
from typing import Dict, Any, Optional
from pathlib import Path


def run_command(
    command: str,
    cwd: Optional[str] = None,
    timeout: int = 120
) -> Dict[str, Any]:
    """
    Execute a command via subprocess and return real results.
    
    Args:
        command: The command to execute (string for shell=True)
        cwd: Working directory for command execution
        timeout: Maximum seconds to wait (default 120)
    
    Returns:
        Dict with:
        - command: str (the command executed)
        - exit_code: int (return code)
        - stdout: str (captured standard output)
        - stderr: str (captured standard error)
        - success: bool (True if exit_code == 0)
        - wall_time: float (execution time in seconds)
        - error: str (error message if exception occurred)
    """
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        wall_time = time.time() - start_time
        
        return {
            "command": command,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
            "wall_time": wall_time,
            "error": None
        }
    
    except subprocess.TimeoutExpired as e:
        wall_time = time.time() - start_time
        return {
            "command": command,
            "exit_code": -1,
            "stdout": e.stdout.decode('utf-8', errors='replace') if e.stdout else "",
            "stderr": f"Command timeout after {timeout} seconds",
            "success": False,
            "wall_time": wall_time,
            "error": f"TimeoutExpired: {timeout}s"
        }
    
    except Exception as e:
        wall_time = time.time() - start_time
        return {
            "command": command,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False,
            "wall_time": wall_time,
            "error": f"{type(e).__name__}: {str(e)}"
        }


def run_command_in_project(
    command: str,
    project_path: Optional[str] = None,
    timeout: int = 120
) -> Dict[str, Any]:
    """
    Execute a command within a project directory.
    
    Args:
        command: The command to execute
        project_path: Project directory (if None, uses current directory)
        timeout: Maximum seconds to wait
    
    Returns:
        Command execution result dict
    """
    
    if project_path:
        # Ensure path exists
        if not Path(project_path).exists():
            return {
                "command": command,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Project path does not exist: {project_path}",
                "success": False,
                "wall_time": 0,
                "error": "PathNotFoundError"
            }
    
    return run_command(command, cwd=project_path, timeout=timeout)


def format_result_for_display(result: Dict[str, Any]) -> str:
    """
    Format command result into a readable string for agent feedback.
    
    Args:
        result: Command execution result dict
    
    Returns:
        Formatted string with command output
    """
    
    lines = []
    lines.append(f"Command: {result['command']}")
    lines.append(f"Exit Code: {result['exit_code']}")
    lines.append(f"Wall Time: {result['wall_time']:.2f}s")
    lines.append(f"Success: {result['success']}")
    
    if result.get('error'):
        lines.append(f"Error: {result['error']}")
    
    if result['stdout']:
        lines.append("\n--- STDOUT ---")
        lines.append(result['stdout'])
    
    if result['stderr']:
        lines.append("\n--- STDERR ---")
        lines.append(result['stderr'])
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Test examples
    print("Test 1: Simple echo command")
    result = run_command("echo 'Hello, World!'")
    print(format_result_for_display(result))
    print()
    
    print("Test 2: Python version")
    result = run_command("python --version")
    print(format_result_for_display(result))
    print()
    
    print("Test 3: Timeout test")
    result = run_command("sleep 5", timeout=2)
    print(format_result_for_display(result))
