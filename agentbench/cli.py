import typer
from pathlib import Path

app = typer.Typer(no_args_is_help = True)

@app.command()
def run_task(task: Path, out: Path = Path('artifacts')):
    typer.echo(f"Running task {task} to {out}")



