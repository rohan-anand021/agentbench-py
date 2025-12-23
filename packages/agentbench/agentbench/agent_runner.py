from datetime import datetime
from pathlib import Path

import ulid

from agentbench.agents.base import Agent
from agentbench.agents.scripted import ScriptedAgent
from agentbench.sandbox.docker_sandbox import DockerSandbox
from agentbench.schemas.attempt_record import (
    AttemptRecord,
    BaselineValidationResult,
    LimitsConfig,
    TaskResult,
    TimestampInfo,
)
from agentbench.scoring import FailureReason
from agentbench.tasks.models import TaskSpec
from agentbench.tasks.validator import validate_baseline


def run_agent_attempt(
    task: TaskSpec,
    workspace_dir: Path,
    artifacts_dir: Path
    ) -> AttemptRecord:
    """
    Run an agent attempt on a task.
    
    Flow:
    1. Run baseline validation (tests should fail)
    2. Instantiate agent based on task.agent.entrypoint
    3. Call agent.run() with failing output
    4. Run final tests
    5. Record attempt
    """

    run_id = str(ulid())
    started_at = datetime.now()
    
    result = None
    validation_result = None
    failure_reason = None
    exit_code = -1

    def get_agent(
        entrypoint: str,
        run_id: str
    ) -> Agent:
        agents = {
            "scripted": ScriptedAgent
        }

        if entrypoint not in agents:
            raise ValueError(
                f"Unknown agent entrypoint: {entrypoint}"
            )
        
        return agents[entrypoint](run_id = run_id)

    try:
        sandbox = DockerSandbox(
            image = task.environment.docker_image,
            workdir = task.environment.workdir
        )

        validation_result = validate_baseline(
            task = task,
            workspace_dir = workspace_dir,
            logs_dir = artifacts_dir / "logs"
        )

        if validation_result.exit_code == 0:
            raise ValueError(
                "baseline validation passed unexpectedly - task is invalid"
            )

        agent = get_agent(
            entrypoint = task.agent.entrypoint,
            run_id = run_id
        )

        result = agent.run(
            task = task,
            sandbox = sandbox,
            workspace_root = workspace_dir,
            artifacts_dir = artifacts_dir,
            failing_output = validation_result.stderr_path.read_text() if validation_result.stderr_path else ""
        )

        exit_code = result.exit_code

    except KeyboardInterrupt:
        failure_reason = FailureReason.INTERRUPTED
    except Exception:
        failure_reason = FailureReason.UNKNOWN

    ended_at = datetime.now()

    return AttemptRecord(
        run_id = run_id,
        task_id = task.id,
        suite = task.suite,
        timestamps = TimestampInfo(
            started_at = started_at,
            ended_at = ended_at
        ),
        duration_sec = (ended_at - started_at).total_seconds(),
        baseline_validation = BaselineValidationResult(
            attempted = validation_result is not None,
            failure_as_expected = validation_result.exit_code != 0 if validation_result else False,
            exit_code = validation_result.exit_code if validation_result else -1
        ),
        result = TaskResult(
            passed = result.success if result else False,
            exit_code = exit_code,
            failure_reason = failure_reason or (FailureReason.from_pytest_exit_code(exit_code) if result and not result.success else None)
        ),
        artifact_paths = {
            "patch_files": ",".join(result.patch_files) if result else ""
        },
        variant = "baseline",
        model = None,
        limits = LimitsConfig(
            timeout_sec = task.environment.timeout_sec,
            tool_timeout_sec = None
        ),
        schema_version = "0.1.0"
    )





    


    

    

