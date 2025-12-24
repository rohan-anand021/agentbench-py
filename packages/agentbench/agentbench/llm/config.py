from enum import StrEnum
from pydantic import BaseModel, Field, SecretStr
from typing import Any

class LLMProvider(StrEnum):
    OPENROUTER = "openrouter"

class SamplingParams(BaseModel):
    temperature: float = Field(
        default = 0.0,
        ge = 0.0,
        le = 2.0
    )
    top_p: float = Field(
        default = 1.0,
        ge = 0.0,
        le = 1.0
    )
    max_tokens: int = Field(
        default = 4096,
        ge = 1,
        le = 128000
    )
    stop_sequences: list[str] | None = None

