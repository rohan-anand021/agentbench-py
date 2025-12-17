import json
import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import ulid
import yaml

from agentbench.sandbox.docker_sandbox import DockerSandbox
from agentbench.util.paths import ensure_dir
from agentbench.tasks.validation import validate_task_yaml
from agentbench.util.process import run_command

logger = logging.getLogger(__name__)


def run_task(
    task_yaml: Path,
    out_dir: Path,
    str_format: str = "%Y-%m-%d_%H-%M-%S",
) -> Path:
    logger.info("Loading task from %s", task_yaml)

    with open(task_yaml) as f:
        task = yaml.safe_load(f)

    # validate keys
    validate_task_yaml(task, task_yaml)

    logger.debug("Task validated successfully: %s", task.get("id", "unknown"))

    out_dir = ensure_dir(out_dir)
    runs_dir = ensure_dir(Path(out_dir / "runs"))

    timestamp = datetime.now().strftime(str_format)
    run_id = str(ulid.new())

    logger.info("Starting run %s for task %s", run_id, task.get("id", "unknown"))

    curr_run_dir = ensure_dir(Path(runs_dir, f"{timestamp}__{run_id}"))

    task_dir = ensure_dir(Path(curr_run_dir, "task"))
    logs_dir = ensure_dir(Path(curr_run_dir, "logs"))
    workspace_dir = ensure_dir(Path(curr_run_dir, "workspace"))

    # copying task_yaml into task
    shutil.copy(task_yaml, task_dir)

    # create workspace/repo
    repo_dir = ensure_dir(Path(workspace_dir, "repo"))

    # clone the repo
    logger.info("Cloning repository from %s", task["repo"]["url"])
    cmd = ["git", "clone", task["repo"]["url"], str(repo_dir)]
    timeout = 120
    stdout_path, stderr_path, exit_code = run_command(
        "git_clone", cmd, timeout, logs_dir
    )

    if exit_code != 0:
        logger.error("Git clone failed with exit code %d", exit_code)
        raise ValueError("git clone operation failed")

    logger.debug("Repository cloned successfully")

    # checkout the commit
    logger.info("Checking out commit %s", task["repo"]["commit"])
    cmd = ["git", "checkout", task["repo"]["commit"]]
    timeout = 120
    stdout_path, stderr_path, exit_code = run_command(
        "git_checkout", cmd, timeout, logs_dir, cwd=repo_dir
    )

    if exit_code != 0:
        logger.error("Git checkout failed with exit code %d", exit_code)
        raise ValueError("git checkout operation failed")

    logger.debug("Commit checked out successfully")

    logger.info("Initializing Docker sandbox with image %s", task["environment"]["docker_image"])
    sandbox = DockerSandbox(
        image=task["environment"]["docker_image"],
        workdir=task["environment"]["workdir"],
    )

    setup_commands = " && ".join(task["setup"]["commands"])
    repo_relative_path = "repo"
    setup_commands = f"cd {repo_relative_path} && {setup_commands}"

    logger.info("Running setup commands")
    logger.debug("Setup commands: %s", setup_commands)
    setup_run_result = sandbox.run(
        workspace_host_path=workspace_dir,
        command=setup_commands,
        network="bridge",
        timeout_sec=task["environment"]["timeout_sec"],
        stdout_path=Path(logs_dir, "setup_stdout.txt"),
        stderr_path=Path(logs_dir, "setup_stderr.txt"),
    )

    if setup_run_result.exit_code != 0:
        logger.error("Setup failed with exit code %d", setup_run_result.exit_code)
        raise ValueError("Setup run failed, please try again")

    logger.debug("Setup completed successfully")

    run_cmd = task["run"]["command"]
    run_cmd = f"cd repo && {run_cmd}"

    logger.info("Running task command")
    logger.debug("Run command: %s", run_cmd)
    run_run_result = sandbox.run(
        workspace_host_path=workspace_dir,
        command=run_cmd,
        network="none",
        timeout_sec=task["environment"]["timeout_sec"],
        stdout_path=Path(logs_dir, "run_stdout.txt"),
        stderr_path=Path(logs_dir, "run_stderr.txt"),
    )

    try:
        digest_cmd = subprocess.run(
            [
                "docker",
                "image",
                "inspect",
                task["environment"]["docker_image"],
                "--format={{.Id}}",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        if digest_cmd.returncode != 0:
            err = digest_cmd.stderr.strip()
            image_digest = f"Image digest unavailable: {err}"
        else:
            image_digest = (
                digest_cmd.stdout.strip()
                or "Image digest unavailable: empty output"
            )

    except subprocess.TimeoutExpired as e:
        image_digest = f"Process timed out: {str(e)}"
    except OSError as e:
        image_digest = f"Docker unavailable: {str(e)}"

    run_data = {
        "run_id": run_id,
        "task_id": task["id"],
        "repo_url": task["repo"]["url"],
        "repo_commit": task["repo"]["commit"],
        "docker_image": task["environment"]["docker_image"],
        "docker_image_digest": image_digest,
        "network_settings": {"Setup": "bridge", "Run": "none"},
        "commands_executed": {
            "setup": task["setup"]["commands"],
            "run": task["run"]["command"],
        },
        "exit_codes": {
            "Setup exit code": str(setup_run_result.exit_code),
            "Run exit code": str(run_run_result.exit_code),
        },
        "paths_to_logs": str(logs_dir),
    }

    runs_path = Path(curr_run_dir, "run.json")
    with runs_path.open("w", encoding="utf-8") as runs:
        json.dump(run_data, runs, indent=2)

    logger.info(
        "Run completed (exit code: %s). Artifacts saved to %s",
        run_run_result.exit_code,
        curr_run_dir,
    )

    return curr_run_dir
