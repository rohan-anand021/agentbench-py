from pathlib import Path
from datetime import datetime
from agentbench.tools.contract import (
    ListFilesParams, 
    ReadFileParams,
    ToolResult, 
    ToolName, 
    ToolError, 
    ToolStatus
)
from agentbench.sandbox.filesystem import safe_glob, resolve_safe_path

def list_files(
    request_id: str,
    workspace_root: Path,
    params: ListFilesParams
) -> ToolResult:
    """
    List files in a directory within the workspace.
    
    Returns files in deterministic sorted order.
    Filters out .git directory by default.
    """

    if params.glob is None:
        params.glob = '*'
    
    error = None
    data = None
    started_at = datetime.now()

    try:
        root_path = resolve_safe_path(
            workspace_root = workspace_root,
            relative_path = params.root
        )

        files = safe_glob(
            workspace_root = root_path,
            pattern = params.glob
        )

        data = {"files": [str(f) for f in files]}
    
    except Exception as e:
        error = e
    
    finally:
        ended_at = datetime.now()

        return ToolResult(
            request_id = request_id,
            tool = ToolName.LIST_FILES,
            status = ToolStatus.SUCCESS if not error else ToolStatus.ERROR,
            started_at = started_at,
            ended_at = ended_at,
            duration_sec = (ended_at - started_at).total_seconds(),
            data = data,
            error = ToolError(
                error_type = type(error).__name__,
                message = str(error),
                details = {f"Error {type(error).__name__}": f"{str(error)}"}
            ) if error else None,
            exit_code = None,
            stdout_path = None,
            stderr_path = None
        )


def read_file(
    workspace_root: Path,
    params: ReadFileParams
) -> ToolResult:

    """
    Read file contents with optional line range.
    
    Line numbers are 1-indexed and inclusive.
    Truncates large files with clear metadata.
    """

    try:
        root_path = resolve_safe_path(
            workspace_root = workspace_root,
            relative_path = params.path
        )

        file_content = ""

        with root_path.open('r') as f:
            for i, line in enumerate(f, start = 1):
                file_content += line.strip() + "\n"

                


            






