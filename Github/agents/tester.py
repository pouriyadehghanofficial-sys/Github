import sys
from pathlib import Path
import json
import subprocess
import importlib.util
import traceback


ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


from tools.file_tools import (
    write_file,
    list_files,
    get_project_path
)

from tools.terminal_tools import (
    run_command_in_project,
    format_result_for_display
)

from memory import (
    load_state,
    save_state,
    add_test,
    add_issue
)



PROJECT_PATH = ROOT / "project"



# =========================
# Find Files
# =========================

def find_python_files():

    project = get_project_path()
    files = []

    if project.exists():

        for file in project.rglob("*.py"):

            if "__pycache__" not in str(file):

                files.append(file)


    return files




# =========================
# Run Python
# =========================

def run_file(file):

    try:

        result=subprocess.run(

            [
                "python",
                str(file)
            ],

            capture_output=True,

            text=True,

            timeout=60

        )


        return {

            "file":str(file),

            "status":
                "PASS"
                if result.returncode==0
                else "FAIL",

            "stdout":result.stdout,

            "stderr":result.stderr,

            "return_code":result.returncode

        }


    except Exception as e:


        return {

            "file":str(file),

            "status":"ERROR",

            "error":str(e)

        }




# =========================
# Import Test
# =========================

def test_import(file):

    try:

        spec=importlib.util.spec_from_file_location(

            file.stem,

            file

        )


        module=importlib.util.module_from_spec(
            spec
        )


        spec.loader.exec_module(
            module
        )


        return {

            "file":str(file),

            "status":"IMPORT_PASS"

        }


    except Exception:


        return {

            "file":str(file),

            "status":"IMPORT_FAIL",

            "error":traceback.format_exc()

        }




# =========================
# Class Test
# =========================

def test_classes(file):

    results=[]


    try:


        spec=importlib.util.spec_from_file_location(

            file.stem,

            file

        )


        module=importlib.util.module_from_spec(
            spec
        )


        spec.loader.exec_module(
            module
        )



        for name in dir(module):


            obj=getattr(
                module,
                name
            )



            if isinstance(obj,type):


                try:

                    instance=obj()


                except Exception as e:


                    results.append({

                        "class":name,

                        "status":"INIT_FAILED",

                        "error":str(e)

                    })

                    continue




                methods=[

                    x for x in dir(instance)

                    if not x.startswith("_")

                    and callable(
                        getattr(instance,x)
                    )

                ]



                for method in methods:


                    try:


                        output=getattr(
                            instance,
                            method
                        )()



                        results.append({

                            "class":name,

                            "method":method,

                            "status":"PASS",

                            "output":str(output)

                        })



                    except Exception as e:


                        results.append({

                            "class":name,

                            "method":method,

                            "status":"FAIL",

                            "error":str(e)

                        })



    except Exception:


        results.append({

            "file":str(file),

            "status":"ERROR",

            "error":traceback.format_exc()

        })



    return results




# =========================
# Run pytest - REAL EXECUTION
# =========================

def run_pytest():

    project = get_project_path()
    tests_path = project / "tests"


    if not tests_path.exists():

        return {

            "status":"SKIPPED",

            "message":"No tests folder",
            "exit_code": None,
            "stdout": "",
            "stderr": ""

        }


    # Use real terminal execution (FIX 2)
    result = run_command_in_project(
        "pytest tests -v",
        project_path=str(project),
        timeout=120
    )

    return {
        "status": "PASS" if result["success"] else "FAIL",
        "exit_code": result["exit_code"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "wall_time": result["wall_time"],
        "error": result.get("error")
    }




# =========================
# Run pip install - REAL EXECUTION
# =========================

def install_dependencies():
    """
    Install project dependencies (requirements.txt if exists).
    Uses real terminal execution.
    """
    
    project = get_project_path()
    req_file = project / "requirements.txt"
    
    if not req_file.exists():
        return {
            "status": "SKIPPED",
            "message": "No requirements.txt found",
            "exit_code": None
        }
    
    result = run_command_in_project(
        "pip install -r requirements.txt",
        project_path=str(project),
        timeout=300
    )
    
    return {
        "status": "PASS" if result["success"] else "FAIL",
        "exit_code": result["exit_code"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "wall_time": result["wall_time"],
        "error": result.get("error")
    }




# =========================
# Report
# =========================

def create_report(data):


    report="""

# Software Test Report


"""


    report+="## Dependency Installation\n\n"
    
    install_result = data.get("install", {})
    report += f"""
Status: {install_result.get('status', 'UNKNOWN')}
Exit Code: {install_result.get('exit_code', 'N/A')}

{install_result.get('stderr', install_result.get('message', ''))}

------------------

"""


    report+="## Python File Execution\n\n"


    for item in data["execution"]:


        report+=f"""

File:
{item.get('file')}


Status:
{item.get('status')}


Error:
{item.get('stderr','')}

------------------

"""



    report+="\n## Import Tests\n\n"



    for item in data["imports"]:


        report+=f"""

File:
{item.get('file')}


Status:
{item.get('status')}


------------------

"""



    report+="\n## Class Tests\n\n"



    for item in data["classes"]:


        report+=f"""

Class:
{item.get('class')}


Method:
{item.get('method')}


Status:
{item.get('status')}


Output:
{item.get('output',item.get('error',''))}


------------------

"""



    report+="\n## Pytest Results\n\n"
    
    pytest_data = data["pytest"]
    report += f"""
Status: {pytest_data.get('status', 'UNKNOWN')}
Exit Code: {pytest_data.get('exit_code', 'N/A')}
Wall Time: {pytest_data.get('wall_time', 'N/A')}s

"""
    
    if pytest_data.get('stdout'):
        report += f"""
### Output
```
{pytest_data['stdout']}
```

"""
    
    if pytest_data.get('stderr'):
        report += f"""
### Errors
```
{pytest_data['stderr']}
```

"""
    
    if pytest_data.get('error'):
        report += f"\nExecution Error: {pytest_data['error']}\n"


    return report




# =========================
# Tester Agent - REAL EXECUTION
# =========================

def tester_agent(task):


    print("\nScanning project...")


    files = find_python_files()



    if not files:


        return {
            "status": "blocked",
            "message": "No python files found"
        }




    execution=[]

    imports=[]

    classes=[]




    for file in files:


        print(
            "Testing:",
            file
        )


        execution.append(

            run_file(file)

        )


        imports.append(

            test_import(file)

        )


        classes.extend(

            test_classes(file)

        )


    # Install dependencies first (FIX 3)
    print("\nInstalling dependencies...")
    install_result = install_dependencies()

    # Run pytest with REAL execution (FIX 3)
    print("\nRunning pytest...")
    pytest_result = run_pytest()



    results = {
        "execution": execution,
        "imports": imports,
        "classes": classes,
        "pytest": pytest_result,
        "install": install_result
    }




    report = create_report(results)




    result = write_file.invoke({

        "path": "docs/test_report.md",

        "content": report

    })




    # Memory update


    add_test(results)



    for item in execution:


        if item["status"] != "PASS":

            add_issue(item)

    
    # Determine overall status
    all_passed = (
        pytest_result.get("status") == "PASS"
        and install_result.get("status") in ["PASS", "SKIPPED"]
        and all(e.get("status") == "PASS" for e in execution)
    )
    
    overall_status = "done" if all_passed else (
        "blocked" if pytest_result.get("status") == "SKIPPED" 
        else "failed"
    )


    return {
        "status": overall_status,
        "summary": f"Pytest: {pytest_result.get('status')}, Files: {len([e for e in execution if e.get('status') == 'PASS'])}/{len(execution)}",
        "report_file": "docs/test_report.md",
        "result": result
    }




if __name__=="__main__":


    while True:


        task=input(

            "\nTester Task: "

        )



        if task.lower()=="exit":

            break



        result=tester_agent(
            task
        )


        print(
            "\nRESULT:"
        )


        print(result)
