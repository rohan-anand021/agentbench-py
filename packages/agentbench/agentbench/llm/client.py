from abc import ABC, abstractmethod
from agentbench.llm.config import LLMConfig
from agentbench.llm.messages import Message, LLMResponse, ToolDefinition

class LLMClient(ABC):
    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None
    ) -> LLMResponse:
        pass
    
    @abstractmethod
    def count_tokens(
        self,
        messages: list[Message]
    ) -> int:
        pass
    
    @property
    def model_name(self) -> str:
        return self.config.provider_config.model_name
    
    @property
    def provider(self) -> str:
        return self.config.provider_config.provider.value
