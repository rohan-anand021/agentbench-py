from enum import StrEnum
from agentbench.scoring.taxonomy import FailureReason

class LLMErrorType(StrEnum):
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    AUTH_FAILED = "auth_failed"
    INVALID_REQUEST = "invalid_request"
    INVALID_RESPONSE = "invalid_response"
    CONTEXT_LENGTH = "context_length"
    CONTENT_FILTER = "content_filter"
    PROVIDER_ERROR = "provider_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"

class LLMError(Exception):
    def __init__(
        self,
        error_type: LLMErrorType,
        message: str,
        provider_code: str | None = None,
        retryable: bool = False,
        details: dict | None = None
    ):
        super().__init__(message)
        self.error_type = error_type
        self.provider_code = provider_code
        self.retryable = retryable
        self.details = details or {}
        
    def to_failure_reason(self) -> FailureReason:
        return FailureReason.LLM_ERROR


class RateLimitedError(LLMError):
    def __init__(
        self,
        message: str,
        retry_after_sec: int | None = None
    ):
        super().__init__(
            LLMErrorType.RATE_LIMITED,
            message,
            retryable = True,
            details = {
                "retry_after_sec": retry_after_sec
            }
        )

class AuthenticationError(LLMError):
    def __init__(
        self,
        message: str,
    ):
        super().__init__(
            LLMErrorType.AUTH_FAILED,
            message,
            retryable = False,
        )

class TimeoutError(LLMError):
    def __init__(
        self,
        message: str
    ):
        super().__init__(
            LLMErrorType.TIMEOUT,
            message,
            retryable = True,
        )

class ContextLengthError(LLMError):
    def __init__(
        self,
        message: str,
        tokens_used: int | None = None
    ):
        super().__init__(
            LLMErrorType.CONTEXT_LENGTH,
            message,
            retryable = False,
            details = {
                "tokens_used": tokens_used
            }
        )
        

    
