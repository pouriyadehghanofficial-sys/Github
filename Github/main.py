from langchain_ollama import ChatOllama
import json

from tools import (
    write_file,
    read_file,
    list_files
)


llm = ChatOllama(
    model="qwen2.5-coder:7b",
    temperature=0
)


def execute_action(response):

    try:
        # حذف markdown code block
        response = response.replace("```json", "")
        response = response.replace("```", "")
        response = response.strip()

        data = json.loads(response)

    except Exception as e:
        return f"Invalid JSON: {e}"


    action = data.get("name")
    args = data.get("arguments", {})


    if action == "write_file":
        return write_file.invoke(args)

    elif action == "read_file":
        return read_file.invoke(args)

    elif action == "list_files":
        return list_files.invoke(args)

    else:
        return "Unknown action"

while True:

    task=input("\nTask: ")

    if task=="exit":
        break


    prompt=f"""
You are a project agent.

Available actions:

1. write_file
arguments:
path, content

2. read_file
arguments:
path

3. list_files
no arguments


User request:
{task}


Return ONLY JSON.
No explanation.

Example:

{{
"name":"write_file",
"arguments":
{{
"path":"test.txt",
"content":"hello"
}}
}}
"""


    result=llm.invoke(prompt)


    output=result.content


    print("\nMODEL:")
    print(output)


    print("\nEXECUTION:")
    print(
        execute_action(output)
    )