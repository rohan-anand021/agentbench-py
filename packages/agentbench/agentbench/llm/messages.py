from enum import StrEnum
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any

class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class Message(BaseModel):
    role: MessageRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]

class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]

class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cached_tokens: int | None = None

class LLMResponse(BaseModel):
    request_id: str
    content: str | None
    tool_calls: list[ToolCall] | None
    finish_reason: str | None
    usage: TokenUsage | None
    latency_ms: int
    timestamp: datetime

    @property
    def has_tool_calls(self) -> bool:
        return self.tool_calls is not None and len(self.tool_calls) > 0
