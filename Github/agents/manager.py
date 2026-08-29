import sys
from pathlib import Path
import json
import re


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



from tools.file_tools import (
    create_project,
    set_active_project
)


from memory import (
    set_memory_project,
    update_project,
    load_state,
    save_state
)





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

    "git_manager": git_manager_agent

}





# ==============================
# Clean Project Name
# ==============================


def clean_project_name(name):


    if not name:

        return "new_project"



    name = str(name)


    name = re.sub(
        r"[^a-zA-Z0-9_-]",
        "_",
        name
    )


    return name.lower()





# ==============================
# Validate Plan
# ==============================


def validate_plan(plan):


    if not isinstance(plan, dict):

        return False


    if "plan" not in plan:

        return False


    if not isinstance(
        plan["plan"],
        list
    ):

        return False



    for step in plan["plan"]:


        if "agent" not in step:

            return False


        if "task" not in step:

            return False



    return True






# ==============================
# Workflow Memory
# ==============================


def save_workflow_step(
        agent,
        task,
        status
):


    try:


        state = load_state()


        if "workflow" not in state:

            state["workflow"] = []



        state["workflow"].append(

            {

                "agent":agent,

                "task":task,

                "status":status

            }

        )


        save_state(state)



    except Exception:

        pass






# ==============================
# Main Workflow
# ==============================


def run_workflow(project_request):


    print(
        "\n========== PROJECT PLANNING =========="
    )



    # 1 Planner

    plan = create_plan(
        project_request
    )



    if not validate_plan(plan):

        return {

            "error":
            "Planner returned invalid plan"

        }




    # 2 Create Project


    project_name = clean_project_name(

        plan.get(

            "project_name",

            "new_project"

        )

    )



    print(
        "\nNEW PROJECT:",
        project_name
    )




    create_project.invoke(

        {

            "name":
            project_name

        }

    )



    set_active_project.invoke(

        {

            "name":
            project_name

        }

    )



    # فعال کردن Memory همین پروژه

    set_memory_project(
        project_name
    )



    update_project(

        project_name,

        project_request

    )



    print(

        f"""

Project Created:

projects/{project_name}

"""

    )






    print(

        "\n========== PLAN =========="

    )


    print(

        json.dumps(

            plan,

            indent=2,

            ensure_ascii=False

        )

    )






    results=[]



    print(

        "\n========== EXECUTION =========="

    )






    # اجرای Agentها به ترتیب Planner


    for step in plan["plan"]:



        agent_name = step["agent"]


        task = step["task"]




        print(

            f"""

===============================

RUNNING {agent_name.upper()}

===============================

"""

        )





        agent = AGENTS.get(
            agent_name
        )



        if agent is None:


            result = {

                "error":
                "Agent not found"

            }


            status="NOT_FOUND"



        else:


            try:


                result = agent(
                    task
                )


                status="SUCCESS"



            except Exception as e:


                result = {

                    "error":
                    str(e)

                }


                status="FAILED"







        save_workflow_step(

            agent_name,

            task,

            status

        )





        results.append(

            {

                "agent":
                agent_name,


                "status":
                status,


                "result":
                result

            }

        )



        print(

            "\nRESULT:"

        )


        print(result)









    # پایان پروژه


    state = load_state()



    state["project"]["status"] = "completed"



    save_state(
        state
    )




    print(

        """

========== PROJECT FINISHED ==========

"""

    )




    return {


        "project":

        project_name,


        "status":

        "completed",


        "results":

        results

    }








# ==============================
# Start
# ==============================


if __name__ == "__main__":



    while True:


        request=input(

            "\nProject Request: "

        )



        if request.lower()=="exit":

            break




        result = run_workflow(

            request

        )



        print(

            "\nFINAL REPORT:"

        )


        print(

            json.dumps(

                result,

                indent=2,

                ensure_ascii=False

            )

        )