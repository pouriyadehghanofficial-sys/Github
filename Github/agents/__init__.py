import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


# Expose output_validator module for package-level access
from . import output_validator

# Re-export terminal tools for convenience
from tools.terminal_tools import (
    run_command,
    run_command_in_project,
    format_result_for_display
)

__all__ = [
    "output_validator",
    "run_command",
    "run_command_in_project",
    "format_result_for_display",
]
