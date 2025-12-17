from pathlib import Path

import typer

from agentbench.logging import setup_logging
from agentbench.run_task import run_task

app = typer.Typer(no_args_is_help=True)

# Initialize logging when the CLI module is loaded
setup_logging()


@app.command("run-task")
def run_task_cmd(
    task: Path = typer.Argument(
        ...,
        help="Path to the task YAML file",
    ),
    out: Path = typer.Option(
        Path("artifacts"),
        "--out",
        "-o",
        help="Output directory for artifacts",
    ),
):
    """
    Execute a task defined in a YAML file.

    This command runs a task inside a Docker container, captures all output,
    and stores the results in an artifact directory with a unique run ID.
    """
    path = run_task(task, out)
    typer.echo(f"Run completed. Artifacts saved to: {path}")


@app.callback()
def main():
    """
    AgentBench: A framework for running and evaluating AI agents.

    Run tasks in isolated Docker containers and capture results.
    """
    pass
