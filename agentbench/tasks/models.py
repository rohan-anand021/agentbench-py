from pathlib import Path

from pydantic import BaseModel


class RepoSpec(BaseModel):
    url: str
    commit: str


class EnvironmentSpec(BaseModel):
    docker_image: str
    workdir: str
    timeout_sec: int


class SetupSpec(BaseModel):
    commands: list[str]


class RunSpec(BaseModel):
    command: str


class TaskSpec(BaseModel):
    id: str
    suite: str
    repo: RepoSpec
    environment: EnvironmentSpec
    setup: SetupSpec
    run: RunSpec
    source_path: Path


# ---


class ValidationResult(BaseModel):
    """
    Define `ValidationResult` dataclass:
    - `task_id: str`
    - `valid: bool` (True if baseline fails as expected)
    - `exit_code: int`
    - `stdout_path: Path`
    - `stderr_path: Path`
    - `error_reason: str | None` (e.g., "baseline_passed", "setup_failed", "timeout")
    - `duration_sec: float`
    """

    task_id: str
    valid: bool
    exit_code: int
    stdout_path: Path
    stderr_path: Path
    error_reason: str | None
    duration_sec: float
