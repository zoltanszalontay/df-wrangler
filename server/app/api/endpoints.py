from fastapi import APIRouter, UploadFile, File, Body
from fastapi.responses import StreamingResponse
from ..services.dataframe_service import dataframe_service
from ..services.code_execution_service import code_execution_service
from ..services.session_service import session_service
from ..services.milvus_service import milvus_service
import pandas as pd
import io
import os

router = APIRouter()


@router.post("/command")
def handle_command(payload: dict = Body(...)):
    user_prompt = payload.get("prompt")
    if not user_prompt:
        return {"error": "Prompt cannot be empty"}, 400

    # Access llm_service from the router object
    llm_service = router.llm_service

    # 1. Classify the command
    classified_command = llm_service.classify_and_extract_command(user_prompt)
    command = classified_command.get("command")
    args = classified_command.get("args", {})

    # 2. Route to the correct logic
    if command == "upload":
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        app_dir = os.path.dirname(current_file_dir)
        server_dir = os.path.dirname(app_dir)
        project_root = os.path.dirname(server_dir)
        file_path = args.get("file_path")

        # Resolve the path to an absolute path from the project root
        if not os.path.isabs(file_path):
            file_path = os.path.join(project_root, file_path)

        # Respond to the client, telling it to perform the upload
        return {"action": "upload", "file_path": file_path}

    elif command == "rename":
        old_name = args.get("old_name")
        new_name = args.get("new_name")
        dataframe_service.rename_dataframe(old_name, new_name)
        return {"message": f"DataFrame {old_name} renamed to {new_name}"}

    elif command == "pop":
        state = dataframe_service.pop_state()
        if state is not None:
            if not state:
                session_service.pop_to_empty_state()
            return {"message": "State popped successfully."}
        else:
            return {"message": "No previous state to pop to."}

    elif command == "remove":
        df_name = args.get("df_name")
        if not df_name:
            return {"error": "DataFrame name is required for removal."}, 400

        if dataframe_service.remove_dataframe(df_name):
            if not dataframe_service.get_all_dataframes():
                session_service.remove_last_dataframe()
            return {"message": f"DataFrame '{df_name}' removed successfully."}
        else:
            return {"error": f"DataFrame '{df_name}' not found."}

    elif command == "download":
        df_name = args.get("df_name")
        filename = args.get("filename")
        if not df_name or not filename:
            return {"error": "DataFrame name and filename are required for download."}, 400

        # Construct the download URL
        # NOTE: This assumes the server is running at http://127.0.0.1:8000
        download_url = f"http://127.0.0.1:8000/download/{df_name}/{filename}"
        return {"download_url": download_url}

    elif command == "list_dataframes":
        dataframes = dataframe_service.get_all_dataframes()
        if dataframes:
            return {"message": "Currently loaded dataframes: " + ", ".join(dataframes.keys())}
        else:
            return {"message": "No dataframes currently loaded."}

    elif command == "analyze":
        if not session_service.active:
            return {"error": "No dataframes loaded. Please upload a dataframe first."}
        
        analysis_prompt = args.get("prompt", user_prompt)
        is_code, content = llm_service.generate_code(analysis_prompt)

        if is_code:
            result = code_execution_service.execute(content, dataframe_service)
            milvus_service.add_conversation_turn(analysis_prompt, content, str(result))
            # Check if the result is a dictionary containing a plot_url
            if isinstance(result, dict) and "plot_url" in result:
                return {"plot_url": result["plot_url"], "code": content}
            else:
                return {"result": str(result), "code": content}
        else:
            milvus_service.add_conversation_turn(analysis_prompt, "", content)
            return {"message": content}

    else:
        return {"error": "Unknown command"}, 400


@router.post("/execute_upload")
def execute_upload(file: UploadFile = File(...)):
    """This endpoint is called by the client *after* the server has
    instructed it to upload a file."""
    try:
        df_name = file.filename.split(".")[0]
        contents = file.file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        dataframe_service.add_dataframe(df_name, df)
        session_service.load_dataframe()
        return {"message": f"DataFrame '{df_name}' created successfully."}
    except Exception as e:
        return {"error": f"Failed to upload and process file: {e}"}, 500


@router.get("/download/{df_name}/{filename}")
def download_dataframe(df_name: str, filename: str):
    """
    Downloads a dataframe as a CSV file.
    """
    df = dataframe_service.get_dataframe(df_name)
    if df is None:
        return {"error": "DataFrame not found"}, 404

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@router.delete("/dataframes/{df_name}")
def remove_dataframe(df_name: str):
    """
    Removes a dataframe.
    """
    if dataframe_service.remove_dataframe(df_name):
        if not dataframe_service.get_all_dataframes():
            session_service.remove_last_dataframe()
        return {"message": f"DataFrame '{df_name}' removed successfully."}
    else:
        return {"error": f"DataFrame '{df_name}' not found."}
