from pathlib import Path
from langchain_core.tools import tool
import subprocess


PROJECT_PATH = Path("./projects/current_project")


@tool
def list_files():
    """
    List all files in project
    """

    files = []

    if not PROJECT_PATH.exists():
        return "Project folder is empty"

    for f in PROJECT_PATH.rglob("*"):
        if f.is_file():
            files.append(str(f.relative_to(PROJECT_PATH)))

    return "\n".join(files)



@tool
def read_file(path: str):
    """
    Read a file from project
    """

    file_path = PROJECT_PATH / path

    if not file_path.exists():
        return f"File not found: {path}"

    return file_path.read_text(
        encoding="utf-8"
    )



@tool
def write_file(path: str, content: str):
    """
    Write content to a project file
    """

    file_path = PROJECT_PATH / path

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path.write_text(
        content,
        encoding="utf-8"
    )

    return f"Saved: {path}"



@tool
def run_test(command: str):
    """
    Run command inside project folder
    """

    try:

        result = subprocess.run(
            command,
            shell=True,
            cwd=PROJECT_PATH,
            capture_output=True,
            text=True,
            timeout=60
        )

        return f"""
RETURN CODE:
{result.returncode}

STDOUT:
{result.stdout}

STDERR:
{result.stderr}
"""

    except subprocess.TimeoutExpired:

        return "Test timeout after 60 seconds"


    except Exception as e:

        return f"Test error: {str(e)}"