from argparse import BooleanOptionalAction
from pydantic import BaseModel
from datetime import datetime

class TimestampInfo(BaseModel):
    started_at: datetime
    ended_at: datetime

class BaselineValidationResult(BaseModel):
    attempted: bool
    failure_as_expected: bool
    exit_code: int

class TaskResult(BaseModel):
    passed: bool
    exit_code: int
    failure_reason: str | None
    

class AttemptRecord(BaseModel):
    """
    - Define `AttemptRecord` Pydantic model matching spec:
        ```python
        class AttemptRecord(BaseModel):
            run_id: str
            task_id: str
            suite: str
            timestamps: TimestampInfo  # started_at, ended_at
            duration_sec: float
            baseline_validation: BaselineValidationResult
            result: TaskResult  # passed, exit_code, failure_reason
            artifact_paths: dict[str, str]
        ```
    - Nested models:
        - `TimestampInfo`: `started_at: datetime`, `ended_at: datetime`
        - `BaselineValidationResult`: `attempted: bool`, `failed_as_expected: bool`, `exit_code: int`
        - `TaskResult`: `passed: bool`, `exit_code: int`, `failure_reason: str | None`
    """

    run_id: str
    task_id: str
    suite: str
    timestamps: TimestampInfo
    duration_sec: float
    baseline_validation: BaselineValidationResult
    result: TaskResult
    artifacts_path: dict[str, str]

