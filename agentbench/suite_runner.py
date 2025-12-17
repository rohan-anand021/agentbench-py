from pathlib import Path
from datetime import datetime
import ulid

from agentbench.tasks.loader import load_suite
from agentbench.util.process import ensure_dir
from agentbench.tasks.validator import validate_baseline

def run_suite(suite_name: str, tasks_root: Path, out_dir: Path) -> Path:
    """
    - Function `run_suite(suite_name: str, tasks_root: Path, out_dir: Path) -> Path`:
        - Load all tasks in suite using `load_suite()`
        - Create run directory: `<out_dir>/runs/<timestamp>__<suite>__baseline/`
        - Create `run.json` metadata file with:
        - `run_id: str` (ULID)
        - `suite: str`
        - `started_at: datetime`
        - `task_count: int`
        - `harness_version: str` (git SHA or "dev")
        - For each task:
        - Create task subdirectory
        - Run `validate_baseline()`
        - Append result to `attempts.jsonl`
        - Print progress to console (e.g., "Task 1/5: toy_fail_pytest... VALID")
        - Update `run.json` with:
        - `ended_at: datetime`
        - `valid_count: int`
        - `invalid_count: int`
        - Return run directory path
    """

    tasks = load_suite(
        tasks_root = tasks_root,
        suite_name = suite_name
    )

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    run_dir = ensure_dir(Path(out_dir / "runs" / f'{timestamp}__{suite_name}__baseline'))

    for i, task in enumerate(tasks):
        started_at = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        runs_data = {
            "run_id": str(ulid.new()),
            "suite": suite_name,
            "started_at": started_at,
            "task_count": i,
            "harness_version": task.repo.url,
        }

        #create task subdirectory

        #run validate baseline
        validation_result = validate_baseline(task = task,
                                              workspace_dir = run_dir,
                                              logs_dir = )

        print(f'Task {i}/{len(tasks)}: {}... {str(task.valid)}')

        ended_at = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        runs_data += {
            "ended_at": ended_at,
            "valid_count": ,
            "invalid_count": 
        }

        return run_dir



    



    

    