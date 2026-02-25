"""Tests for OpenAI pricing module."""

import pytest
from trendsleuth.pricing import (
    get_model_pricing,
    estimate_cost,
    get_supported_models,
    MODEL_PRICING,
    DEFAULT_PRICING,
)


class TestPricing:
    """Test suite for pricing module."""

    def test_get_model_pricing_known_model(self):
        """Test getting pricing for a known model."""
        pricing = get_model_pricing("gpt-4o-mini")
        assert pricing == {"input": 0.150, "output": 0.600}

    def test_get_model_pricing_unknown_model(self):
        """Test getting pricing for an unknown model returns default."""
        pricing = get_model_pricing("unknown-model")
        assert pricing == DEFAULT_PRICING

    def test_get_model_pricing_all_models(self):
        """Test that all models in MODEL_PRICING can be retrieved."""
        for model_name in MODEL_PRICING:
            pricing = get_model_pricing(model_name)
            assert "input" in pricing
            assert "output" in pricing
            assert pricing["input"] > 0
            assert pricing["output"] > 0

    def test_estimate_cost_gpt4o_mini(self):
        """Test cost estimation for gpt-4o-mini."""
        cost, is_exact = estimate_cost("gpt-4o-mini", 1000, 500)

        # Calculate expected cost (pricing is per 1M tokens)
        expected = (1000 * 0.150 / 1_000_000) + (500 * 0.600 / 1_000_000)
        assert cost == pytest.approx(expected)
        assert is_exact is True

    def test_estimate_cost_gpt4o(self):
        """Test cost estimation for gpt-4o."""
        cost, is_exact = estimate_cost("gpt-4o", 10000, 5000)

        # Calculate expected cost (pricing is per 1M tokens)
        expected = (10000 * 2.50 / 1_000_000) + (5000 * 10.00 / 1_000_000)
        assert cost == pytest.approx(expected)
        assert is_exact is True

    def test_estimate_cost_o1(self):
        """Test cost estimation for o1 (most expensive model)."""
        cost, is_exact = estimate_cost("o1", 1000, 500)

        # Calculate expected cost (pricing is per 1M tokens)
        expected = (1000 * 15.00 / 1_000_000) + (500 * 60.00 / 1_000_000)
        assert cost == pytest.approx(expected)
        assert is_exact is True

    def test_estimate_cost_unknown_model(self):
        """Test cost estimation for unknown model uses fallback."""
        cost, is_exact = estimate_cost("unknown-model", 1000, 500)

        # Should use default pricing (gpt-4o-mini)
        expected = (1000 * 0.150 / 1_000_000) + (500 * 0.600 / 1_000_000)
        assert cost == pytest.approx(expected)
        assert is_exact is False  # Flag should indicate fallback pricing

    def test_estimate_cost_zero_tokens(self):
        """Test cost estimation with zero tokens."""
        cost, is_exact = estimate_cost("gpt-4o-mini", 0, 0)
        assert cost == 0.0
        assert is_exact is True

    def test_estimate_cost_large_usage(self):
        """Test cost estimation with large token usage."""
        # 1 million input tokens + 500k output tokens
        cost, is_exact = estimate_cost("gpt-4o-mini", 1_000_000, 500_000)

        # Should be: (1M * 0.150 / 1M) + (500k * 0.600 / 1M) = 0.150 + 0.300 = 0.45
        expected = 0.150 + 0.300
        assert cost == pytest.approx(expected)
        assert is_exact is True

    def test_get_supported_models(self):
        """Test getting list of supported models."""
        models = get_supported_models()

        # Should be sorted alphabetically
        assert models == sorted(models)

        # Should contain key models
        assert "gpt-4o-mini" in models
        assert "gpt-4o" in models
        assert "o1" in models
        assert "gpt-4-turbo" in models

        # Should match MODEL_PRICING keys
        assert set(models) == set(MODEL_PRICING.keys())

    def test_model_pricing_structure(self):
        """Test that MODEL_PRICING has correct structure."""
        for model, pricing in MODEL_PRICING.items():
            assert isinstance(model, str)
            assert isinstance(pricing, dict)
            assert "input" in pricing
            assert "output" in pricing
            assert isinstance(pricing["input"], (int, float))
            assert isinstance(pricing["output"], (int, float))
            assert pricing["input"] > 0
            assert pricing["output"] > 0
            # Output pricing should generally be higher than input
            assert pricing["output"] >= pricing["input"]

    def test_pricing_comparison(self):
        """Test pricing comparison between models."""
        gpt4o_mini = get_model_pricing("gpt-4o-mini")
        gpt4o = get_model_pricing("gpt-4o")
        o1 = get_model_pricing("o1")

        # gpt-4o-mini should be cheapest
        assert gpt4o_mini["input"] < gpt4o["input"]
        assert gpt4o_mini["output"] < gpt4o["output"]

        # o1 should be most expensive
        assert o1["input"] > gpt4o["input"]
        assert o1["output"] > gpt4o["output"]
