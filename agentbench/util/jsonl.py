import json
import logging
import os
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path

from filelock import FileLock

logger = logging.getLogger(__name__)


def append_jsonl(path: Path, record: dict):
    """
    - Function `append_jsonl(path: Path, record: dict) -> None`:
        - Open file in append mode
        - Write JSON + newline
        - Use atomic write pattern (write to temp, rename)
        - Handle file locking for concurrent writes (optional, can use `filelock` library)
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lock = FileLock(str(path) + ".lock")

    with lock:
        json_line = json.dumps(record) + "\n"

        with tempfile.NamedTemporaryFile(
            mode="wb", delete=False, dir=path.parent
        ) as tmp:
            tmp_path = Path(tmp.name)

            if path.exists():
                with path.open("rb") as src:
                    shutil.copyfileobj(src, tmp)

            tmp.write(json_line.encode("utf-8"))
            tmp.flush()
            os.fsync(tmp.fileno())

        os.replace(tmp_path, path)


def read_jsonl(path: Path) -> Iterator[dict]:
    """
    Function `read_jsonl(path: Path) -> Iterator[dict]`:
        - Open file, yield one parsed dict per line
        - Skip empty lines
        - Log warning (don't crash) for malformed lines
    """

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line == "":
                continue

            try:
                record = json.loads(line)
                yield record

            except Exception as e:
                logger.warning("Line %s could not be read: %s", line, str(e))
                continue
