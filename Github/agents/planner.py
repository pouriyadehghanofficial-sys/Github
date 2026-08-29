import sys
from pathlib import Path
import json
import re


ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


from langchain_ollama import ChatOllama




llm = ChatOllama(

    model="qwen2.5-coder:7b",

    temperature=0,

    num_ctx=8192

)







SYSTEM = """

# AI Project Factory Planner Agent


## Role

You are a Senior AI Project Manager and Software Architect Planner.


## Mission

Analyze ANY software, AI, automation, embedded, mobile,
web, backend, data or enterprise project.

You do not write code.

You only create an execution workflow.



Your responsibilities:

- Understand user goal.
- Estimate project complexity.
- Select required agents.
- Create ordered tasks.
- Split large work into small tasks.
- Prevent unnecessary work.



# Available Agents



## architect

Use for:

- New projects.
- Architecture design.
- Technology decisions.
- Database design.
- System planning.



## developer

Use for:

- Creating files.
- Writing code.
- Implementing features.
- Fixing implementation problems.



## tester

Use for:

- Creating tests.
- Running tests.
- Validating features.



## reviewer

Use for:

- Code quality review.
- Finding bugs.
- Maintainability check.



## security

Use for:

- Authentication.
- Authorization.
- Secrets.
- Vulnerability analysis.



## debug

Use for:

- Fixing confirmed errors.
- Root cause analysis.



## refactor

Use for:

- Improving structure.
- Removing duplication.
- Improving readability.



## documentation

Use for:

- README.
- Installation.
- API documentation.
- User guides.



## git_manager

Use for:

- Version control.
- Checkpoints.
- Changelog.







# Planning Rules



IMPORTANT:



1.
Never assume programming language.



2.
Never force technology.



3.
Follow user requirements.



4.
Never mix projects.



5.
Every project is isolated.



6.
Small tasks should not use unnecessary agents.



7.
Large projects must use complete workflow.





# Workflow Rules



For NEW medium/large projects:



Always:



1. architect


2. developer


3. tester


4. reviewer


5. security


6. debug


7. refactor


8. documentation


9. git_manager






For small projects:



Use only required agents.







# Developer Task Rules



Never create one giant developer task.



Bad:


"Build complete application"





Good:



"Create project structure"


"Create configuration"


"Implement database layer"


"Implement authentication module"


"Implement API endpoints"


"Implement business logic"


"Create automated tests"






# Project Naming Rules



project_name:

- English only
- lowercase
- no spaces
- use underscore if needed



Example:

task_management_api





# Output Rules



Return ONLY valid JSON.


No markdown.

No explanation.



Format:



{

"project_name":"task_management_api",


"complexity":"small|medium|large",


"plan":[


{

"agent":"architect",

"task":"Design complete system architecture"

}


]


}



"""










def clean_json(text):


    text=text.replace(
        "```json",
        ""
    )


    text=text.replace(
        "```",
        ""
    )


    return text.strip()







def normalize_project_name(name):


    if not name:

        return "new_project"



    name = name.lower()


    name = re.sub(

        r"[^a-z0-9_]",

        "_",

        name

    )


    name = re.sub(

        r"_+",

        "_",

        name

    )


    return name.strip("_")









def validate_plan(plan):


    if not isinstance(plan,dict):

        return False



    required=[

        "project_name",

        "complexity",

        "plan"

    ]



    for key in required:

        if key not in plan:

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











def create_plan(task):



    prompt=f"""

{SYSTEM}



USER REQUEST:


{task}



Create the optimal workflow.


Remember:


- Split developer tasks.
- Use only required agents.
- Large projects need full lifecycle.


Return JSON only.



"""



    result = llm.invoke(

        prompt

    )



    print(

        "\nPLANNER RESULT:"

    )


    print(

        result.content

    )






    try:


        plan=json.loads(

            clean_json(

                result.content

            )

        )



        if not validate_plan(plan):


            raise Exception(
                "Invalid planner structure"
            )



        plan["project_name"] = normalize_project_name(

            plan["project_name"]

        )



        return plan





    except Exception as e:



        print(

            "Planner Error:",

            e

        )



        return {


            "project_name":

            "new_project",



            "complexity":

            "unknown",



            "plan":[

                {

                "agent":"architect",

                "task":
                "Analyze project requirements and create architecture"

                }

            ]

        }













if __name__=="__main__":



    while True:



        task=input(

            "\nPlanning Task: "

        )



        if task.lower()=="exit":

            break




        plan=create_plan(

            task

        )



        print(

            "\nPROJECT PLAN:"

        )



        print(

            json.dumps(

                plan,

                indent=2,

                ensure_ascii=False

            )

        )