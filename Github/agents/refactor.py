import sys
from pathlib import Path
import json


ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


from langchain_ollama import ChatOllama


from tools.file_tools import (
    list_files,
    read_file,
    write_file
)

from agents.tech_stack_utils import format_stack_for_prompt
from memory import (
    add_task,
    load_state,
    get_locked_stack
)




llm = ChatOllama(
    model="qwen2.5-coder:7b",
    temperature=0,
    num_ctx=8192
)




SYSTEM = """

You are a Refactor Agent.

Role:
Improve code structure and quality.

Responsibilities:

- Remove code duplication
- Improve readability
- Optimize performance
- Enhance maintainability
- Apply best practices

Output:
Create refactored code files.

Return ONLY JSON.

"""




def clean_json(text):
    text = text.replace("```json", "")
    text = text.replace("```", "")
    return text.strip()


def execute(action):
    try:
        data = json.loads(clean_json(action))
    except Exception as e:
        return f"JSON ERROR: {e}"

    if isinstance(data, list):
        results = []
        for item in data:
            results.append(execute(json.dumps(item)))
        return "\n".join(results)

    name = data.get("name")
    args = data.get("arguments", {})

    if name == "write_file":
        return write_file.invoke(args)
    elif name == "read_file":
        from tools.file_tools import read_file as read_file_tool
        return read_file_tool.invoke(args)

    return "Unknown action"


def refactor_agent(task):

    print("\nREFACTOR TASK:", task)

    try:
        files = list_files.invoke({})
    except:
        files = "No files"

    try:
        memory = load_state()
    except:
        memory = {}

    locked_stack = get_locked_stack()
    stack_prompt = format_stack_for_prompt(locked_stack)

    prompt = f"""

{SYSTEM}

{stack_prompt}

CURRENT FILES:

{files}

PROJECT MEMORY:

{json.dumps(memory, indent=4, ensure_ascii=False)}

REFACTOR TASK:

{task}

Refactor and improve the code.
Return refactored files as JSON write_file actions.

"""

    response = llm.invoke(prompt)

    print("\nMODEL RESPONSE:")
    print(response.content)

    result = execute(response.content)

    try:
        add_task(task)
    except:
        pass

    return result


if __name__ == "__main__":

    while True:

        task = input("\nRefactor Task: ")

        if task.lower() == "exit":
            break

        result = refactor_agent(task)

        print("\nRESULT:")
        print(result)
