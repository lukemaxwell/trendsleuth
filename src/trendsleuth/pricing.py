"""OpenAI model pricing information."""

# OpenAI pricing as of February 2026 (per 1M tokens)
# Source: https://openai.com/api/pricing/
MODEL_PRICING = {
    # GPT-4o models
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-2024-11-20": {"input": 2.50, "output": 10.00},
    "gpt-4o-2024-08-06": {"input": 2.50, "output": 10.00},
    "gpt-4o-2024-05-13": {"input": 5.00, "output": 15.00},
    # GPT-4o mini models
    "gpt-4o-mini": {"input": 0.150, "output": 0.600},
    "gpt-4o-mini-2024-07-18": {"input": 0.150, "output": 0.600},
    # o1 models
    "o1": {"input": 15.00, "output": 60.00},
    "o1-2024-12-17": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 3.00, "output": 12.00},
    "o1-mini-2024-09-12": {"input": 3.00, "output": 12.00},
    "o1-preview": {"input": 15.00, "output": 60.00},
    "o1-preview-2024-09-12": {"input": 15.00, "output": 60.00},
    # GPT-4 Turbo models
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4-turbo-2024-04-09": {"input": 10.00, "output": 30.00},
    "gpt-4-turbo-preview": {"input": 10.00, "output": 30.00},
    # GPT-4 models
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-4-0613": {"input": 30.00, "output": 60.00},
    "gpt-4-0314": {"input": 30.00, "output": 60.00},
    # GPT-3.5 Turbo models
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "gpt-3.5-turbo-0125": {"input": 0.50, "output": 1.50},
    "gpt-3.5-turbo-1106": {"input": 1.00, "output": 2.00},
    "gpt-3.5-turbo-0613": {"input": 1.50, "output": 2.00},
}

# Default pricing for unknown models (use gpt-4o-mini as fallback)
DEFAULT_PRICING = {"input": 0.150, "output": 0.600}


def get_model_pricing(model: str) -> dict[str, float]:
    """Get pricing for a specific model.

    Args:
        model: OpenAI model name

    Returns:
        Dictionary with 'input' and 'output' pricing per 1M tokens
    """
    return MODEL_PRICING.get(model, DEFAULT_PRICING)


def estimate_cost(
    model: str, prompt_tokens: int, completion_tokens: int
) -> tuple[float, bool]:
    """Estimate API cost based on token usage and model.

    Args:
        model: OpenAI model name
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens

    Returns:
        Tuple of (estimated_cost, is_exact_pricing)
        is_exact_pricing is False if using fallback pricing
    """
    pricing = MODEL_PRICING.get(model)
    is_exact = pricing is not None

    if pricing is None:
        pricing = DEFAULT_PRICING

    # Pricing is per 1M tokens, so divide by 1M
    cost = (
        prompt_tokens * pricing["input"] / 1_000_000
        + completion_tokens * pricing["output"] / 1_000_000
    )

    return cost, is_exact


def get_supported_models() -> list[str]:
    """Get list of models with known pricing.

    Returns:
        List of model names
    """
    return sorted(MODEL_PRICING.keys())
