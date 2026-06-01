import time
from typing import Dict, Any, List
from src.telemetry.logger import logger

class PerformanceTracker:
    """
    Tracking industry-standard metrics for LLMs.
    """
    def __init__(self):
        self.session_metrics = []

    def track_request(self, provider: str, model: str, usage: Dict[str, int], latency_ms: int):
        """
        Logs a single request metric to our telemetry.
        """
        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "completion_to_prompt_ratio": self._completion_to_prompt_ratio(usage),
            "latency_ms": latency_ms,
            "cost_estimate": self._calculate_cost(model, usage),
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        rates_per_1k = {
            "gpt-4o": 0.01,
            "gpt-4o-mini": 0.002,
            "gemini-1.5-flash": 0.0015,
        }
        rate = rates_per_1k.get(model, 0.002)
        return (usage.get("total_tokens", 0) / 1000) * rate

    def _completion_to_prompt_ratio(self, usage: Dict[str, int]) -> float:
        prompt_tokens = usage.get("prompt_tokens", 0)
        if prompt_tokens <= 0:
            return 0.0
        return round(usage.get("completion_tokens", 0) / prompt_tokens, 4)

# Global tracker instance
tracker = PerformanceTracker()
