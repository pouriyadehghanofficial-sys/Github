from langchain_ollama import ChatOllama
import os
import json
from datetime import datetime


# =========================
# تنظیم مدل
# =========================

llm = ChatOllama(
    model="qwen2.5-coder:7b",
    temperature=0
)


# =========================
# مسیرها
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

AGENTS_DIR = os.path.join(BASE_DIR, "agents")
MEMORY_DIR = os.path.join(BASE_DIR, "memory")


# =========================
# خواندن نقش Agent
# =========================

def load_agent(agent_name):

    path = os.path.join(
        AGENTS_DIR,
        agent_name + ".md"
    )

    with open(path, "r", encoding="utf-8") as f:
        return f.read()



# =========================
# حافظه پروژه
# =========================

def update_memory(text):

    path = os.path.join(
        MEMORY_DIR,
        "project_state.md"
    )

    with open(path, "a", encoding="utf-8") as f:

        f.write(
            "\n\n---\n"
            + datetime.now().strftime("%Y-%m-%d %H:%M")
            + "\n"
            + text
        )



# =========================
# اجرای Agent
# =========================

def run_agent(agent, task):

    role = load_agent(agent)


    prompt = f"""

You are this agent:

{role}


Current task:

{task}


Answer according to your role.
"""


    result = llm.invoke(prompt)

    return result.content



# =========================
# مدیر اصلی
# =========================

def manager(task):


    manager_prompt = f"""

You are Project Manager.

Available agents:

architect
developer
reviewer
tester
security
documentation
debugger


User task:

{task}


Choose ONE agent only.

Return ONLY JSON:

{{
"agent":"agent_name",
"reason":"why"
}}

"""


    result = llm.invoke(manager_prompt)


    text = result.content


    text = text.replace("```json","")
    text = text.replace("```","")
    text=text.strip()


    decision=json.loads(text)


    return decision["agent"]




# =========================
# Main Loop
# =========================


while True:


    task=input("\nProject Task: ")


    if task=="exit":
        break



    print("\n[Manager] analyzing...")


    agent=manager(task)


    print(
        "[Selected Agent]:",
        agent
    )


    print("\n[Running Agent]")


    answer=run_agent(
        agent,
        task
    )


    print("\nRESULT:")
    print(answer)


    update_memory(
        f"""
Task:
{task}

Agent:
{agent}

Result:
{answer}
"""
    )