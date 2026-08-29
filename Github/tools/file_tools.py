from pathlib import Path
from langchain_core.tools import tool
import json
import re




ROOT = Path(__file__).resolve().parent.parent


PROJECTS_PATH = ROOT / "projects"

PROJECTS_PATH.mkdir(
    parents=True,
    exist_ok=True
)



ACTIVE_PROJECT_FILE = ROOT / "active_project.json"






# =====================================
# Helpers
# =====================================


def clean_name(name):

    name = re.sub(
        r"[^a-zA-Z0-9_-]",
        "_",
        name
    )

    return name or "default"







def get_project_path():

    """
    Return active project path.
    """


    if not ACTIVE_PROJECT_FILE.exists():

        default = PROJECTS_PATH / "default"

        default.mkdir(
            parents=True,
            exist_ok=True
        )

        return default



    try:


        data=json.loads(

            ACTIVE_PROJECT_FILE.read_text(
                encoding="utf-8"
            )

        )


        path=Path(
            data["path"]
        )


        path.mkdir(
            parents=True,
            exist_ok=True
        )


        return path



    except Exception:


        default = PROJECTS_PATH / "default"


        default.mkdir(
            parents=True,
            exist_ok=True
        )


        return default







def set_active(name):

    """
    Set active project internally.
    """


    name=clean_name(name)


    project_path=PROJECTS_PATH / name


    project_path.mkdir(
        parents=True,
        exist_ok=True
    )


    ACTIVE_PROJECT_FILE.write_text(

        json.dumps(

            {
                "name":name,
                "path":str(project_path)

            },

            indent=4

        ),

        encoding="utf-8"

    )


    return project_path







def safe_path(path):

    """
    Prevent access outside project.
    """


    base=get_project_path()


    target=(base / path).resolve()



    if not str(target).startswith(
        str(base.resolve())
    ):

        raise Exception(
            "Invalid path"
        )


    return target







# =====================================
# List Files
# =====================================


@tool
def list_files():

    """
    List all files inside active project.

    Returns:
        Project file list.
    """


    project=get_project_path()


    files=[]



    for f in project.rglob("*"):


        if (

            f.is_file()

            and

            "__pycache__" not in str(f)

        ):


            files.append(

                str(
                    f.relative_to(project)
                )

            )



    if not files:

        return "Project is empty"



    return "\n".join(files)









# =====================================
# Read File
# =====================================


@tool
def read_file(path:str):

    """
    Read a file from active project.

    Args:
        path:
            Relative file path.
    """


    try:


        file_path=safe_path(path)



        if not file_path.exists():

            return f"File not found: {path}"



        return file_path.read_text(

            encoding="utf-8"

        )


    except Exception as e:


        return f"READ ERROR: {e}"









# =====================================
# Write File
# =====================================


@tool
def write_file(path:str, content:str):

    """
    Create or update a file.

    Args:
        path:
            Relative file path.

        content:
            File content.
    """


    try:


        file_path=safe_path(path)



        file_path.parent.mkdir(

            parents=True,

            exist_ok=True

        )



        file_path.write_text(

            content,

            encoding="utf-8"

        )


        return f"Saved: {path}"



    except Exception as e:


        return f"WRITE ERROR: {e}"









# =====================================
# Delete File
# =====================================


@tool
def delete_file(path:str):

    """
    Delete a file from active project.

    Args:
        path:
            Relative file path.
    """


    try:


        file_path=safe_path(path)



        if not file_path.exists():

            return f"File not found: {path}"



        file_path.unlink()



        return f"Deleted: {path}"



    except Exception as e:


        return f"DELETE ERROR: {e}"









# =====================================
# Create Folder
# =====================================


@tool
def create_folder(path:str):

    """
    Create folder inside active project.

    Args:
        path:
            Folder path.
    """


    try:


        folder=safe_path(path)



        folder.mkdir(

            parents=True,

            exist_ok=True

        )


        return f"Created folder: {path}"



    except Exception as e:


        return f"FOLDER ERROR: {e}"









# =====================================
# Create Project
# =====================================


@tool
def create_project(name:str):

    """
    Create a new isolated project.

    Args:
        name:
            Project name.
    """


    name=clean_name(name)


    project=PROJECTS_PATH / name



    project.mkdir(

        parents=True,

        exist_ok=True

    )



    for folder in [

        "src",

        "tests",

        "docs",

        "config",

        "memory"

    ]:


        (project / folder).mkdir(

            exist_ok=True

        )



    set_active(name)



    return f"Project created and activated: {name}"









# =====================================
# Switch Project
# =====================================


@tool
def set_active_project(name:str):

    """
    Switch current active project.

    Args:
        name:
            Project name.
    """


    path=set_active(name)


    return f"Active project: {path}"