"""
Output validation for agent responses.
Ensures agents return properly structured JSON with no nested JSON in file content.
"""

import json
import re
from typing import Dict, Any, List, Optional


def is_json_like_content(content: str) -> bool:
    """
    Check if content looks like it's a JSON action object instead of file content.
    This catches cases where the LLM put a JSON action inside the content field.
    
    Patterns to detect:
    - Starts with whitespace then { and "name":|"action":|"type":
    - Starts with [ and contains { "name"|"action"|"type"
    """
    content_stripped = content.strip()
    
    # Check for JSON object starting with common action keys
    if re.match(r'^\s*\{\s*["\']?(name|action|type)["\']?\s*:', content_stripped):
        return True
    
    # Check for JSON array of actions
    if re.match(r'^\s*\[\s*\{\s*["\']?(name|action|type)["\']?\s*:', content_stripped):
        return True
    
    return False


def validate_agent_output(output: Any) -> Dict[str, Any]:
    """
    Validate agent output structure.
    
    Expected schema:
    {
        "agent": "<role>",
        "status": "done" | "failed" | "blocked" | "needs_review",
        "actions": [
            {"type": "write_file", "path": "...", "content": "..."},
            {"type": "run_terminal", "command": "..."},
            {"type": "note", "message": "..."}
        ],
        "summary": "..."
    }
    
    Returns:
        Dict with:
        - valid: bool
        - errors: List[str]
        - validated_output: Dict or None
    """
    
    if not isinstance(output, dict):
        return {
            "valid": False,
            "errors": ["Output is not a dictionary"],
            "validated_output": None
        }
    
    errors = []
    
    # Check required fields
    if "status" not in output:
        errors.append("Missing 'status' field")
    elif output["status"] not in ["done", "failed", "blocked", "needs_review"]:
        errors.append(f"Invalid status: {output['status']}")
    
    if "actions" not in output:
        errors.append("Missing 'actions' field")
    elif not isinstance(output["actions"], list):
        errors.append("'actions' must be a list")
    
    # Validate each action
    if "actions" in output and isinstance(output["actions"], list):
        for i, action in enumerate(output["actions"]):
            if not isinstance(action, dict):
                errors.append(f"Action {i} is not a dictionary")
                continue
            
            if "type" not in action:
                errors.append(f"Action {i} missing 'type'")
            elif action["type"] not in ["write_file", "run_terminal", "note"]:
                errors.append(f"Action {i} has invalid type: {action['type']}")
            
            # For write_file actions, check content
            if action.get("type") == "write_file":
                if "path" not in action:
                    errors.append(f"Action {i} (write_file) missing 'path'")
                if "content" not in action:
                    errors.append(f"Action {i} (write_file) missing 'content'")
                elif is_json_like_content(action["content"]):
                    errors.append(
                        f"Action {i} (write_file): content appears to be JSON action object, "
                        "not file content"
                    )
            
            elif action.get("type") == "run_terminal":
                if "command" not in action:
                    errors.append(f"Action {i} (run_terminal) missing 'command'")
            
            elif action.get("type") == "note":
                if "message" not in action:
                    errors.append(f"Action {i} (note) missing 'message'")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "validated_output": output if len(errors) == 0 else None
    }


def extract_actions_from_legacy_format(output: Any) -> Optional[List[Dict[str, Any]]]:
    """
    Extract actions from older agent formats that might use different structures.
    Attempts to be backward compatible with existing agents.
    
    Returns:
        List of normalized actions or None if unable to extract
    """
    if isinstance(output, dict):
        # Check if it's already in new format
        if "actions" in output and isinstance(output["actions"], list):
            return output["actions"]
        
        # Try to extract single action from old-style response
        if "name" in output or "type" in output:
            # Old format: {"name": "write_file", "arguments": {...}}
            name = output.get("name") or output.get("type")
            args = output.get("arguments", {})
            
            if name == "write_file":
                return [{
                    "type": "write_file",
                    "path": args.get("path"),
                    "content": args.get("content")
                }]
            elif name == "run_terminal":
                return [{
                    "type": "run_terminal",
                    "command": args.get("command")
                }]
    
    return None
