import json
from pathlib import Path
from datetime import datetime


ROOT = Path(__file__).resolve().parent.parent


# =========================
# Projects Workspace
# =========================

PROJECTS_PATH = ROOT / "projects"

PROJECTS_PATH.mkdir(
    parents=True,
    exist_ok=True
)


# پروژه فعال فعلی
ACTIVE_PROJECT = "default"





# =========================
# Project Selection
# =========================

def set_memory_project(name):

    """
    Change active project memory.
    """

    global ACTIVE_PROJECT

    ACTIVE_PROJECT = name


    path = (
        PROJECTS_PATH /
        name /
        "memory"
    )


    path.mkdir(
        parents=True,
        exist_ok=True
    )





def get_active_project():

    return ACTIVE_PROJECT





def memory_file():

    path = (
        PROJECTS_PATH /
        ACTIVE_PROJECT /
        "memory"
    )


    path.mkdir(
        parents=True,
        exist_ok=True
    )


    return path / "project_state.json"







# =========================
# Default State
# =========================

def default_state():


    return {


        "project":{

            "name": ACTIVE_PROJECT,

            "description":"",

            "created":
            str(datetime.now()),

            "version":"0.1.0"

        },



        "architecture":{


            "document":"",

            "technologies":[],

            "decisions":[]

        },



        "files":[],


        "completed_tasks":[],


        "tests":[],


        "issues":[],


        "changes":[],


        "agents":{

            "architect":[],
            "developer":[],
            "tester":[],
            "reviewer":[],
            "security":[],
            "debug":[],
            "refactor":[],
            "documentation":[],
            "git_manager":[]

        }

    }







# =========================
# Load / Save
# =========================

def load_state():


    file = memory_file()



    if not file.exists():


        state = default_state()


        save_state(
            state
        )


        return state




    return json.loads(

        file.read_text(
            encoding="utf-8"
        )

    )







def save_state(state):


    file = memory_file()


    file.write_text(

        json.dumps(

            state,

            indent=4,

            ensure_ascii=False

        ),

        encoding="utf-8"

    )








# =========================
# Project Information
# =========================

def update_project(
        name,
        description=""
):


    state = load_state()


    state["project"]["name"] = name


    state["project"]["description"] = description



    save_state(
        state
    )








# =========================
# Files
# =========================

def add_file(path):


    state = load_state()



    if path not in state["files"]:


        state["files"].append(
            path
        )


    save_state(
        state
    )








# =========================
# Tasks
# =========================

def add_task(task):


    state = load_state()



    state["completed_tasks"].append(

        {

            "time":
            str(datetime.now()),


            "task":
            task

        }

    )



    save_state(
        state
    )








# =========================
# Agent History
# =========================

def add_agent_result(
        agent,
        result
):


    state = load_state()



    if agent not in state["agents"]:

        state["agents"][agent] = []



    state["agents"][agent].append(

        {

            "time":
            str(datetime.now()),


            "result":
            str(result)

        }

    )



    save_state(
        state
    )









# =========================
# Architecture
# =========================

def save_architecture(content):


    state = load_state()


    state["architecture"]["document"] = content


    save_state(
        state
    )







def add_decision(decision):


    state = load_state()



    state["architecture"]["decisions"].append(

        {

            "time":
            str(datetime.now()),


            "decision":
            decision

        }

    )


    save_state(
        state
    )








# =========================
# Tests
# =========================

def add_test(result):


    state = load_state()


    state["tests"].append(

        {

            "time":
            str(datetime.now()),


            "result":
            result

        }

    )


    save_state(
        state
    )








# =========================
# Issues
# =========================

def add_issue(issue):


    state = load_state()



    state["issues"].append(

        {

            "time":
            str(datetime.now()),


            "issue":
            issue

        }

    )



    save_state(
        state
    )








# =========================
# Changes
# =========================

def add_change(change):


    state = load_state()



    state["changes"].append(

        {

            "time":
            str(datetime.now()),


            "change":
            change

        }

    )


    save_state(
        state
    )







# =========================
# Memory Viewer
# =========================

def show_memory():


    return load_state()







if __name__ == "__main__":


    print(

        json.dumps(

            load_state(),

            indent=4,

            ensure_ascii=False

        )

    )