import sys
from pathlib import Path
import json
from datetime import datetime


ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


from langchain_ollama import ChatOllama


from tools.file_tools import (
    list_files,
    read_file,
    write_file
)


from memory import (
    add_file,
    add_task,
    add_change,
    load_state
)





llm = ChatOllama(

    model="qwen2.5-coder:7b",

    temperature=0,

    num_ctx=8192

)







SYSTEM = """

# Senior General Purpose Developer Agent


## Role

You are a senior software engineer.


## Mission

Implement ONLY the assigned development task.

You work on the current active project.

You do not redesign architecture.

You do not perform unrelated changes.



## Workflow


Before coding:


1. Read project files.

2. Read architecture document if exists.

3. Understand dependencies.

4. Decide minimal required changes.



Then:


- Create files.
- Modify files.
- Implement complete code.
- Keep existing functionality.






## Rules



NEVER:


- Create fake code.
- Create empty functions.
- Use pass.
- Delete files.
- Rewrite unrelated files.
- Change architecture.
- Create unnecessary files.






For existing files:


Always read before modifying.



For large projects:


Work incrementally.

Create maximum 3 files per task.





## Output



Return ONLY JSON.



Available actions:





Read file:


{
"name":"read_file",
"arguments":{
"path":"file/path"
}
}





List files:


{
"name":"list_files",
"arguments":{}
}





Write file:


{
"name":"write_file",
"arguments":{

"path":"file/path",

"content":"complete code"

}

}





Multiple actions allowed:


[

{

"name":"write_file",

"arguments":{

"path":"file",

"content":"code"

}

}

]



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









def execute(action):


    try:


        data=json.loads(

            clean_json(action)

        )


    except Exception as e:


        return {

            "error":

            f"Invalid JSON: {e}"

        }






    results=[]




    if isinstance(data,list):


        for item in data:


            results.append(

                execute(

                    json.dumps(item)

                )

            )


        return results





    name=data.get(

        "name"

    )


    args=data.get(

        "arguments",

        {}

    )





    if name=="write_file":



        result=write_file.invoke(

            {

                "path":

                args["path"],



                "content":

                args["content"]

            }

        )



        add_file(

            args["path"]

        )


        add_change(

            f"Created or updated {args['path']}"

        )



        return result





    elif name=="read_file":


        return read_file.invoke(

            args

        )





    elif name=="list_files":


        return list_files.invoke(

            {}

        )





    return {

        "error":

        "Unknown action"

    }









def developer_agent(task):



    print(

        "\nDEVELOPER TASK:",

        task

    )




    # Read architecture


    try:


        architecture=read_file.invoke(

            {

                "path":

                "docs/architecture.md"

            }

        )


    except:


        architecture="No architecture document"







    # Current files


    try:


        files=list_files.invoke(

            {}

        )


    except:


        files="No files"







    # Memory


    try:


        memory=load_state()


    except:


        memory={}









    prompt=f"""

{SYSTEM}



PROJECT ARCHITECTURE:


{architecture}



CURRENT FILES:


{files}



PROJECT MEMORY:


{json.dumps(memory,indent=4,ensure_ascii=False)}



ASSIGNED TASK:


{task}



Remember:


- First understand current project.
- Modify only required files.
- Do not create unnecessary files.
- Return JSON actions only.



"""





    response=llm.invoke(

        prompt

    )



    print(

        "\nMODEL RESPONSE:"

    )


    print(

        response.content

    )







    result=execute(

        response.content

    )






    # Save task history


    try:


        add_task(

            task

        )


    except Exception as e:


        print(

            "Memory task error:",

            e

        )






    return result











if __name__=="__main__":



    while True:



        task=input(

            "\nDeveloper Task: "

        )



        if task.lower()=="exit":

            break




        result=developer_agent(

            task

        )


        print(

            "\nRESULT:"

        )


        print(result)