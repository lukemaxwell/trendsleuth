"""Token usage tracking for LangChain LLM calls."""

from typing import Any, Optional
from langchain_core.callbacks import BaseCallbackHandler


class TokenUsageTracker(BaseCallbackHandler):
    """Callback handler to track token usage across LLM calls."""

    def __init__(self) -> None:
        """Initialize the token tracker."""
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.model_name: Optional[str] = None

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Track token usage when LLM call completes."""
        if hasattr(response, "llm_output") and response.llm_output:
            token_usage = response.llm_output.get("token_usage", {})
            self.total_prompt_tokens += token_usage.get("prompt_tokens", 0)
            self.total_completion_tokens += token_usage.get("completion_tokens", 0)
            self.total_tokens += token_usage.get("total_tokens", 0)

            # Capture model name if available
            if not self.model_name and "model_name" in response.llm_output:
                self.model_name = response.llm_output["model_name"]

    def get_usage(self) -> dict[str, int]:
        """Get token usage statistics.

        Returns:
            Dictionary with prompt_tokens, completion_tokens, and total_tokens
        """
        return {
            "input_tokens": self.total_prompt_tokens,
            "output_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
        }

    def reset(self) -> None:
        """Reset all counters."""
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.model_name = None
