# Week 1: Skeleton + Docker Runner

## Goal
By end of week: Run a single task (repo + pytest) inside Docker, capture all output to artifacts, and prove determinism by running twice and comparing results.

---

## Day 1 (Monday): Environment Setup + Project Skeleton

### Prerequisites Verification
- [ ] Verify Docker Desktop is installed and running (`docker ps` works)
- [ ] Verify Docker can run containers (`docker run --rm hello-world`)
- [ ] Verify git is installed and configured
- [ ] Verify Python 3.11+ is available
- [ ] Install uv if not already installed (via official install script)
- [ ] Verify uv works (`uv --version`)

### Project Initialization
- [ ] Create the project root directory structure:
  - `agentbench/` (Python package)
  - `agentbench/sandbox/`
  - `agentbench/util/`
  - `agentbench/schemas/`
  - `docker/py-runner/`
  - `tasks/custom-dev/`
  - `artifacts/`
  - `scripts/`
  - `tests/`
  - `configs/`

- [ ] Create `pyproject.toml` with:
  - Project name: `agentbench-py`
  - Version: `0.1.0`
  - Python requirement: `>=3.11`
  - Dependencies: typer, rich, pydantic, pydantic-settings, httpx, PyYAML, ulid-py
  - Dev dependencies: pytest, ruff
  - Script entry point: `ab = "agentbench.cli:app"`
  - Ruff config: line-length 80, select E/F/I/UP/B

- [ ] Create `.python-version` file with `3.11`

- [ ] Create `.gitignore` with:
  - `.venv/`
  - `__pycache__/`
  - `*.pyc`
  - `artifacts/`
  - `.DS_Store`
  - `.env`
  - `uv.lock` (optional, can be committed)

- [ ] Create `.env.example` with `OPENROUTER_API_KEY=replace_me`

- [ ] Initialize git repository
- [ ] Run `uv venv --python 3.11` to create virtual environment
- [ ] Run `uv sync` to install dependencies
- [ ] Verify installation: `uv run python -c "import typer, yaml, pydantic"`

### End of Day 1 Checkpoint
- [ ] `uv run python -c "import typer"` succeeds
- [ ] Directory structure exists
- [ ] Git repo initialized with first commit

---

## Day 2 (Tuesday): Docker Runner Image + Basic CLI

### Docker Runner Image
- [ ] Create `docker/py-runner/Dockerfile`:
  - Base image: `python:3.11-slim`
  - Install system packages: git, build-essential (for compiling pip packages)
  - Create non-root user `runner` with UID 1000
  - Set working directory to `/workspace`
  - Set environment variables:
    - `PIP_DISABLE_PIP_VERSION_CHECK=1`
    - `PIP_NO_INPUT=1`
    - `PYTHONDONTWRITEBYTECODE=1`
    - `PYTHONUNBUFFERED=1`

- [ ] Build the image: tag as `ghcr.io/agentbench/py-runner:0.1.0`
- [ ] Test the image: run `python -V` inside container
- [ ] Test the image: verify it runs as non-root user
- [ ] Document the image in `docker/py-runner/README.md`:
  - What's included
  - How to build
  - How to verify

### Minimal CLI Skeleton
- [ ] Create `agentbench/__init__.py` (empty, makes it a package)
- [ ] Create `agentbench/cli.py`:
  - Initialize Typer app with `no_args_is_help=True`
  - Add placeholder `run-task` command that accepts:
    - `--task` (path to task.yaml, required)
    - `--out` (output directory, defaults to `artifacts`)
  - Command should just print the arguments for now

- [ ] Verify CLI works: `uv run ab --help` shows help
- [ ] Verify CLI works: `uv run ab run-task --help` shows command help

### End of Day 2 Checkpoint
- [ ] Docker image builds successfully
- [ ] `docker run --rm ghcr.io/agentbench/py-runner:0.1.0 python -V` outputs Python 3.11.x
- [ ] `docker run --rm ghcr.io/agentbench/py-runner:0.1.0 whoami` outputs `runner`
- [ ] `uv run ab --help` shows CLI help

---

## Day 3 (Wednesday): Utility Modules + Docker Sandbox Class

### Utility Module: Paths
- [ ] Create `agentbench/util/__init__.py`
- [ ] Create `agentbench/util/paths.py`:
  - Function `ensure_dir(path: Path) -> Path`: creates directory if not exists, returns path
  - This is a simple helper used everywhere

### Docker Sandbox Module
- [ ] Create `agentbench/sandbox/__init__.py`
- [ ] Create `agentbench/sandbox/docker_sandbox.py`:
  - Define `DockerRunResult` dataclass with fields:
    - `exit_code: int`
    - `stdout_path: Path`
    - `stderr_path: Path`
  
  - Define `DockerSandbox` class:
    - Constructor takes `image: str` and `workdir: str` (default `/workspace`)
    - Method `run()` that:
      - Accepts: `workspace_host_path`, `command`, `network`, `timeout_sec`, `stdout_path`, `stderr_path`
      - Builds docker run command with:
        - `--rm` (auto-remove container)
        - `--network` flag (none/bridge)
        - Volume mount: host workspace → container workdir
        - Working directory set to workdir
        - Command executed via `bash -lc` (login shell for proper env)
      - Executes via `subprocess.run()`
      - Captures stdout/stderr to the specified file paths
      - Handles timeout: if `subprocess.TimeoutExpired`, write timeout marker to stderr, return exit code 124
      - Returns `DockerRunResult`

### Test the Sandbox Manually
- [ ] Create a temporary test directory with a simple Python file
- [ ] Write a quick test script that:
  - Instantiates `DockerSandbox`
  - Calls `run()` with `python -V`
  - Verifies stdout file contains version
  - Verifies exit code is 0

### End of Day 3 Checkpoint
- [ ] `DockerSandbox.run()` can execute commands in container
- [ ] stdout/stderr are captured to files
- [ ] Timeout handling works (test with `sleep 10` and 2 second timeout)
- [ ] Exit codes are captured correctly

---

## Day 4 (Thursday): Toy Repo + Task Spec + Task Runner

### Create Toy Test Repository
- [ ] Create `examples/toy_repo/` directory
- [ ] Initialize git repo inside it
- [ ] Create structure:
  - `pyproject.toml` (minimal, with setuptools)
  - `src/toy/__init__.py`
  - `src/toy/mathy.py` with a function `add(a, b)` that's intentionally broken (returns `a - b`)
  - `tests/test_basic.py` with test that calls `add(2, 3)` and asserts result is 5

- [ ] Commit everything and record the commit SHA
      - a3219a9adc9f143c379d38d76a77cd969380f90d
- [ ] Verify: running pytest in this repo should FAIL (this is intentional)

### Task Spec for Toy Repo
- [ ] Create `tasks/custom-dev/toy_fail_pytest/task.yaml`:
  - `id`: "toy_fail_pytest"
  - `suite`: "custom-dev"
  - `repo.url`: relative path to `examples/toy_repo` (or file:// URL)
  - `repo.commit`: the SHA you recorded
  - `environment.docker_image`: the py-runner image tag
  - `environment.workdir`: "/workspace"
  - `environment.network`: "none"
  - `environment.timeout_sec`: 300
  - `setup.commands`: pip upgrade, pip install pytest, pip install -e .
  - `run.command`: "pytest -q"

### Task Runner Module
- [ ] Create `agentbench/run_task.py`:
  - Function `run_task(task_yaml: Path, out_dir: Path) -> Path`:
    - Load task.yaml using PyYAML
    - Generate run ID using ULID
    - Create artifact directory structure:
      - `artifacts/runs/<timestamp>__<run_id>/`
      - Subdirs: `task/`, `logs/`, `workspace/`
    - Copy task.yaml into `task/` directory (freeze the spec)
    
    - **Git operations**:
      - Clone the repo URL into `workspace/repo/`
      - Checkout the pinned commit
      - Log git stdout/stderr to `logs/git_clone_*.txt` and `logs/git_checkout_*.txt`
      - Fail gracefully if clone/checkout fails
    
    - **Setup phase**:
      - Instantiate `DockerSandbox`
      - Join all setup commands with ` && `
      - Run in container with network=bridge (allow pip to download)
      - Capture to `logs/setup_stdout.txt`, `logs/setup_stderr.txt`
    
    - **Run phase**:
      - Run the `run.command` in container
      - Use network=none (isolated)
      - Capture to `logs/run_stdout.txt`, `logs/run_stderr.txt`
    
    - **Metadata**:
      - Create `run.json` with:
        - run_id
        - task_id
        - repo_url, repo_commit
        - docker_image
        - network settings
        - commands executed
        - exit codes for setup and run
        - paths to logs
    
    - Return the run directory path

### Wire Up CLI
- [ ] Update `agentbench/cli.py`:
  - Import `run_task` function
  - `run-task` command should call `run_task()` and print the result path

### End of Day 4 Checkpoint
- [ ] `uv run ab run-task --task tasks/custom-dev/toy_fail_pytest/task.yaml` executes
- [ ] Artifact directory is created with all expected files
- [ ] `run.json` contains all metadata
- [ ] `logs/run_stdout.txt` shows pytest failure output
- [ ] Exit code in `run.json` is 1 (failing test)

---

## Day 5 (Friday): Doctor Script + Determinism Proof + Polish

### Doctor Script
- [ ] Create `scripts/doctor.sh`:
  - Check docker is available: `docker version`
  - Check docker can run containers: `docker run --rm hello-world`
  - Check the py-runner image exists: `docker image inspect ghcr.io/agentbench/py-runner:0.1.0`
  - Check git is available: `git --version`
  - Check Python version: `python3 --version`
  - Check disk space: warn if < 10GB free
  - Print success/failure summary with colors (green/red)
  - Exit 0 if all pass, exit 1 if any fail

- [ ] Make it executable: `chmod +x scripts/doctor.sh`
- [ ] Test: `./scripts/doctor.sh` passes

### Determinism Proof
- [ ] Run the task twice:
  - `uv run ab run-task --task tasks/custom-dev/toy_fail_pytest/task.yaml`
  - `uv run ab run-task --task tasks/custom-dev/toy_fail_pytest/task.yaml`

- [ ] Verify determinism:
  - Both runs create separate artifact directories (different timestamps/ULIDs)
  - Both have the same exit code (1)
  - Both `run_stdout.txt` show the same pytest failure
  - Both `run.json` have consistent metadata (same commit, image, commands)

- [ ] Document: Add to notes what varies (timestamps, run IDs) vs what's stable (exit codes, error messages)

### Capture Docker Image Digest
- [ ] Enhance `run_task.py` to also capture:
  - Docker image digest: run `docker image inspect --format='{{.Id}}'` and store in `run.json`
  - This proves which exact image was used

### Polish and Documentation
- [ ] Create `artifacts/.gitkeep` so the directory is tracked but empty
- [ ] Update CLI help strings to be descriptive
- [ ] Add docstrings to main functions
- [ ] Run ruff: `uv run ruff check agentbench/`
- [ ] Fix any linting issues
- [ ] Run ruff format: `uv run ruff format agentbench/`

### Week 1 Commit
- [ ] Stage all changes
- [ ] Commit with message: "Week 1: docker runner + single-task execution with artifacts"
- [ ] Verify: `git log --oneline` shows the commit

### End of Day 5 / Week 1 Checkpoint
- [ ] `./scripts/doctor.sh` passes all checks
- [ ] `uv run ab run-task --task ...` works end-to-end
- [ ] Two runs produce:
  - Different artifact directories
  - Same exit codes
  - Same test output
  - Captured docker image digest
- [ ] All code passes ruff linting
- [ ] Week 1 commit is made

---

## Week 1 Success Criteria (Summary)

| Criterion | How to Verify |
|-----------|---------------|
| Docker image builds | `docker run --rm ghcr.io/agentbench/py-runner:0.1.0 python -V` |
| CLI works | `uv run ab --help` shows commands |
| Task runs | `uv run ab run-task --task tasks/.../task.yaml` completes |
| Artifacts created | `ls artifacts/runs/` shows timestamped directories |
| Logs captured | `cat artifacts/runs/.../logs/run_stdout.txt` shows pytest output |
| Metadata recorded | `cat artifacts/runs/.../run.json` shows all fields |
| Determinism | Two runs have same exit code and similar logs |
| Image digest captured | `run.json` includes docker image ID |

---

## Architecture Decisions Made This Week

1. **subprocess over docker-py**: Using `subprocess` to call docker CLI directly. Simpler to debug, easier to see exactly what commands run.

2. **bash -lc for commands**: Running commands via `bash -lc` ensures login shell environment is loaded (important for pip, pyenv, etc.).

3. **ULID for run IDs**: Using ULID instead of UUID because ULIDs are sortable by time and more readable.

4. **Separate setup and run phases**: Setup runs with network=bridge (for pip), run phase uses network=none (isolated).

5. **Freeze task.yaml in artifacts**: Copy the task spec into the artifact directory so you always know exactly what config was used.

6. **stdout/stderr to files**: Capture to files rather than memory to handle large outputs and allow post-hoc inspection.

7. **exit code 124 for timeout**: Following standard convention (like GNU timeout) for timeout exit codes.

---

## Files Created This Week

```
agentbench/
  __init__.py
  cli.py
  run_task.py
  sandbox/
    __init__.py
    docker_sandbox.py
  util/
    __init__.py
    paths.py

docker/
  py-runner/
    Dockerfile
    README.md

examples/
  toy_repo/
    pyproject.toml
    src/toy/__init__.py
    src/toy/mathy.py
    tests/test_basic.py

tasks/
  custom-dev/
    toy_fail_pytest/
      task.yaml

scripts/
  doctor.sh

artifacts/
  .gitkeep

pyproject.toml
.python-version
.gitignore
.env.example
```

---

## Potential Blockers & Mitigations

| Blocker | Mitigation |
|---------|------------|
| Docker Desktop not running | Add to doctor.sh, document in README |
| Image build fails | Pin base image digest, document expected output |
| Relative path issues with repo URL | Use absolute paths or `file://` URLs |
| Git clone fails | Log full stderr, check network |
| Container runs as root | Verify Dockerfile USER directive, test with whoami |
| Timeout not working | Test explicitly with `sleep` command |

