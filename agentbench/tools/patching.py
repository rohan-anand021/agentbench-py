from dataclasses import dataclass
from pathlib import Path

@dataclass
class PatchHunk:
    old_start: int
    old_count: int