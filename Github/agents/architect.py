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


from memory import (
    add_decision,
    save_architecture,
    add_task
)




llm = ChatOllama(
    model="qwen2.5-coder:7b",
    temperature=0
)






SYSTEM = """

You are a Senior Software Architect AI Agent.


Role:

Design professional architecture for ANY software project.


You analyze:

- Requirements
- Existing code
- Technologies
- Data flow
- System structure
- Risks


You do NOT write source code.


You create architecture documents only.



You support:

- Web applications
- APIs
- AI systems
- Mobile applications
- Data platforms
- Automation
- Embedded systems
- Enterprise software



Responsibilities:

- Select technologies.
- Define modules.
- Define components.
- Define database if needed.
- Define APIs if needed.
- Define security architecture.
- Define development phases.



Rules:

- Never assume project type.
- Never invent requirements.
- Use existing project information.
- Return ONLY JSON.
- No markdown outside JSON.



Available action:



write_file:


{
"name":"write_file",

"arguments":{

"path":"docs/architecture.md",

"content":"architecture document"

}

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







def execute(action):


    try:


        data=json.loads(
            clean_json(action)
        )


    except Exception as e:


        return f"JSON ERROR: {e}"





    if isinstance(data,list):


        results=[]


        for item in data:


            results.append(

                execute(

                    json.dumps(item)

                )

            )


        return "\n".join(results)







    name=data.get(
        "name"
    )


    args=data.get(
        "arguments",
        {}
    )





    if name=="write_file":


        return write_file.invoke(
            args
        )



    return "Unknown action"









def architect_agent(task):


    files=list_files.invoke({})




    try:


        previous=read_file.invoke(

            {

            "path":
            "docs/architecture.md"

            }

        )


    except:


        previous="No previous architecture"







    prompt=f"""

{SYSTEM}



CURRENT PROJECT FILES:


{files}




PREVIOUS ARCHITECTURE:


{previous}




PROJECT REQUEST:


{task}




Create architecture document.



Required sections:



1. Project Overview


2. Requirements Analysis


3. System Architecture


4. Components


5. Technology Stack


6. Database Design


7. API Design


8. Security Design


9. Development Roadmap


10. Risks


11. Future Improvements




Return ONLY JSON:



{{
"name":"write_file",

"arguments":{{

"path":"docs/architecture.md",

"content":"complete architecture"

}}

}}



"""





    response=llm.invoke(
        prompt
    )



    print("\nMODEL:")
    print(response.content)




    result=execute(
        response.content
    )




    # ذخیره در Memory


    try:


        add_task(
            task
        )


        save_architecture(

            response.content

        )


        add_decision(

            "Architecture created"

        )


    except Exception:


        pass




    return result











if __name__=="__main__":



    while True:



        task=input(
            "\nArchitect Task: "
        )


        if task.lower()=="exit":

            break



        result=architect_agent(
            task
        )



        print("\nRESULT:")
        print(result)