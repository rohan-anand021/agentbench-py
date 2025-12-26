import httpx
from datetime import datetime, timezone
from agentbench.llm.client import LLMClient
from agentbench.llm.config import LLMConfig
from agentbench.llm.messages import (
    InputItem,
    ToolDefinition,
    LLMResponse,
)
from agentbench.llm.errors import AuthenticationError, LLMError, LLMErrorType, TimeoutError

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/responses"

class OpenRouterClient(LLMClient):

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client: httpx.AsyncClient | None = None

    def _get_headers(self) -> dict[str, str]:
        api_key = self.config.provider_config.api_key

        if not api_key:
            raise AuthenticationError("API key is required")

        return {
            "Authorization": f"Bearer {api_key.get_secret_value()}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/agentbench",
            "X-Title": "AgentBench"
        }

    def _build_request_body(
        self,
        input_items: list[InputItem],
        tools: list[ToolDefinition] | None = None
    ) -> dict:
        body = {
            "model": self.model_name,
            "input": [item.model_dump(
                mode = "json") for item in input_items],
            "max_output_tokens": self.config.sampling.max_tokens,
            "temperature": self.config.sampling.temperature,
            "top_p": self.config.sampling.top_p,
        }

        if tools:
            body["tools"] = [tool.model_dump(
                mode = "json") for tool in tools]
            body["tool_choice"] = "auto"
        
        return body
    
    def _parse_response(
        self,
        response_data: dict,
        latency_ms: int
    ) -> LLMResponse:
        pass

    def _classify_error(
        self,
        status_code: int,
        response_body: dict | None
    ) -> LLMError:
        error_map = {
            401: (LLMErrorType.AUTH_FAILED, False),
            402: (LLMErrorType.AUTH_FAILED, False),
            403: (LLMErrorType.AUTH_FAILED, False),
            429: (LLMErrorType.RATE_LIMITED, True),
            500: (LLMErrorType.PROVIDER_ERROR, True),
            502: (LLMErrorType.PROVIDER_ERROR, True),
            503: (LLMErrorType.PROVIDER_ERROR, True),
        } 

        error_type, retryable = error_map.get(status_code, (LLMErrorType.PROVIDER_ERROR, True))

        message = response_body.get("error", {}).get("message", f"HTTP {status_code}") if response_body else f"HTTP {status_code}"

        return LLMError(error_type, message, retryable = retryable)

    async def complete(
        self,
        input_items: list[InputItem],
        tools: list[ToolDefinition] | None = None
    ) -> LLMResponse:
        start_time = datetime.now(timezone.utc)

        async with httpx.AsyncClient(
            timeout = self.config.provider_config.timeout_sec
        ) as client:
            try:
                response = await client.post(
                    OPENROUTER_API_URL,
                    headers = self._get_headers(),
                    json = self._build_request_body(input_items, tools)
                )
                
                if response.status_code != 200:
                    raise self._classify_error(response.status_code, response.json())
                
                latency_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

                return LLMResponse.model_validate({
                    **response.json(),
                    "latency_ms": latency_ms
                })
            
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out after {self.config.provider_config.timeout_sec} seconds") from e
            except httpx.HTTPStatusError as e:
                raise self._classify_error(e.response.status_code, e.response.json()) from e
            except httpx.RequestError as e:
                raise LLMError(LLMErrorType.NETWORK_ERROR, str(e), retryable = True) from e
            except Exception as e:
                raise LLMError(LLMErrorType.PROVIDER_ERROR, str(e)) from e

    
    def count_tokens(
        self,
        input_items: list[InputItem],
        tools: list[ToolDefinition] | None = None
    ) -> int:
        return len(input_items) + len(tools) if tools else len(input_items)