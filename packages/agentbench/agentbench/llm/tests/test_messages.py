"""Unit tests for LLM message types.

Tests cover:
1. Message serialization
2. ToolCall arguments validation
3. LLMResponse.has_tool_calls property
4. LLMResponse round-trip serialization
5. TokenUsage totals
"""

import pytest
from datetime import datetime, timezone

from agentbench.llm.messages import (
    MessageRole,
    Message,
    ToolDefinition,
    ToolCall,
    TokenUsage,
    LLMResponse,
)


class TestMessageSerialization:
    """Tests for Message serialization."""

    def test_message_serialization(self) -> None:
        """Message.model_dump(mode='json') works correctly."""
        message = Message(
            role=MessageRole.USER,
            content="Hello, how are you?",
            name=None,
            tool_call_id=None,
        )

        serialized = message.model_dump(mode="json")

        assert serialized["role"] == "user"
        assert serialized["content"] == "Hello, how are you?"
        assert serialized["name"] is None
        assert serialized["tool_call_id"] is None

    def test_message_with_tool_info_serialization(self) -> None:
        """Message with tool information serializes correctly."""
        message = Message(
            role=MessageRole.TOOL,
            content="Tool result here",
            name="search",
            tool_call_id="call_123",
        )

        serialized = message.model_dump(mode="json")

        assert serialized["role"] == "tool"
        assert serialized["name"] == "search"
        assert serialized["tool_call_id"] == "call_123"

    def test_all_message_roles(self) -> None:
        """All MessageRole values can be used."""
        roles = [MessageRole.USER, MessageRole.ASSISTANT, MessageRole.SYSTEM, MessageRole.TOOL]
        
        for role in roles:
            message = Message(role=role, content="test")
            assert message.role == role


class TestToolCallArguments:
    """Tests for ToolCall arguments validation."""

    def test_tool_call_arguments_are_dict(self) -> None:
        """ToolCall.arguments validates as dict."""
        tool_call = ToolCall(
            id="call_abc123",
            name="read_file",
            arguments={"path": "/src/main.py", "encoding": "utf-8"},
        )

        assert isinstance(tool_call.arguments, dict)
        assert tool_call.arguments["path"] == "/src/main.py"
        assert tool_call.arguments["encoding"] == "utf-8"

    def test_tool_call_empty_arguments(self) -> None:
        """ToolCall accepts empty dict for arguments."""
        tool_call = ToolCall(
            id="call_xyz",
            name="list_files",
            arguments={},
        )

        assert tool_call.arguments == {}

    def test_tool_call_nested_arguments(self) -> None:
        """ToolCall arguments can contain nested structures."""
        tool_call = ToolCall(
            id="call_nested",
            name="complex_tool",
            arguments={
                "options": {"verbose": True, "limit": 100},
                "filters": ["*.py", "*.txt"],
            },
        )

        assert tool_call.arguments["options"]["verbose"] is True
        assert len(tool_call.arguments["filters"]) == 2


class TestLLMResponseHasToolCalls:
    """Tests for LLMResponse.has_tool_calls property."""

    def test_llm_response_has_tool_calls_true(self) -> None:
        """has_tool_calls returns True when tool_calls is non-empty list."""
        response = LLMResponse(
            request_id="req_123",
            content=None,
            tool_calls=[
                ToolCall(id="call_1", name="search", arguments={"query": "test"})
            ],
            finish_reason="tool_calls",
            usage=None,
            latency_ms=150,
            timestamp=datetime.now(timezone.utc),
        )

        assert response.has_tool_calls is True

    def test_llm_response_has_tool_calls_false_none(self) -> None:
        """has_tool_calls returns False when tool_calls is None."""
        response = LLMResponse(
            request_id="req_456",
            content="Hello there!",
            tool_calls=None,
            finish_reason="stop",
            usage=None,
            latency_ms=100,
            timestamp=datetime.now(timezone.utc),
        )

        assert response.has_tool_calls is False

    def test_llm_response_has_tool_calls_false_empty(self) -> None:
        """has_tool_calls returns False when tool_calls is empty list."""
        response = LLMResponse(
            request_id="req_789",
            content="Response with empty tools",
            tool_calls=[],
            finish_reason="stop",
            usage=None,
            latency_ms=120,
            timestamp=datetime.now(timezone.utc),
        )

        assert response.has_tool_calls is False


class TestLLMResponseSerialization:
    """Tests for LLMResponse serialization round-trip."""

    def test_llm_response_serialization(self) -> None:
        """LLMResponse can round-trip through JSON serialization."""
        original = LLMResponse(
            request_id="req_roundtrip",
            content="Test response content",
            tool_calls=None,
            finish_reason="stop",
            usage=TokenUsage(
                prompt_tokens=50,
                completion_tokens=25,
                total_tokens=75,
            ),
            latency_ms=200,
            timestamp=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        )

        # Serialize to JSON
        json_dict = original.model_dump(mode="json")

        # Deserialize back
        restored = LLMResponse.model_validate(json_dict)

        assert restored.request_id == original.request_id
        assert restored.content == original.content
        assert restored.finish_reason == original.finish_reason
        assert restored.latency_ms == original.latency_ms
        assert restored.usage is not None
        assert restored.usage.prompt_tokens == 50

    def test_llm_response_with_tool_calls_roundtrip(self) -> None:
        """LLMResponse with tool_calls can round-trip through JSON."""
        original = LLMResponse(
            request_id="req_tools",
            content=None,
            tool_calls=[
                ToolCall(id="call_a", name="read_file", arguments={"path": "/test.py"}),
                ToolCall(id="call_b", name="search", arguments={"query": "def main"}),
            ],
            finish_reason="tool_calls",
            usage=None,
            latency_ms=300,
            timestamp=datetime.now(timezone.utc),
        )

        json_dict = original.model_dump(mode="json")
        restored = LLMResponse.model_validate(json_dict)

        assert restored.tool_calls is not None
        assert len(restored.tool_calls) == 2
        assert restored.tool_calls[0].name == "read_file"
        assert restored.tool_calls[1].name == "search"


class TestTokenUsageTotals:
    """Tests for TokenUsage totals validation."""

    def test_token_usage_totals(self) -> None:
        """Total tokens equals prompt + completion tokens."""
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        )

        assert usage.total_tokens == usage.prompt_tokens + usage.completion_tokens

    def test_token_usage_with_cached(self) -> None:
        """TokenUsage with cached_tokens works correctly."""
        usage = TokenUsage(
            prompt_tokens=200,
            completion_tokens=100,
            total_tokens=300,
            cached_tokens=50,
        )

        assert usage.cached_tokens == 50
        assert usage.total_tokens == 300

    def test_token_usage_cached_optional(self) -> None:
        """cached_tokens is optional and defaults to None."""
        usage = TokenUsage(
            prompt_tokens=50,
            completion_tokens=25,
            total_tokens=75,
        )

        assert usage.cached_tokens is None


class TestToolDefinition:
    """Tests for ToolDefinition model."""

    def test_tool_definition_serialization(self) -> None:
        """ToolDefinition serializes correctly."""
        tool_def = ToolDefinition(
            name="read_file",
            description="Read the contents of a file",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to read"},
                },
                "required": ["path"],
            },
        )

        serialized = tool_def.model_dump(mode="json")

        assert serialized["name"] == "read_file"
        assert serialized["description"] == "Read the contents of a file"
        assert "properties" in serialized["parameters"]
