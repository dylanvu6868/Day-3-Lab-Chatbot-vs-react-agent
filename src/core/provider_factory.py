import os
from dotenv import load_dotenv


def build_provider():
    load_dotenv()
    provider = os.getenv("DEFAULT_PROVIDER", "openai").strip().lower()
    model = os.getenv("DEFAULT_MODEL", "gpt-4o-mini").strip()

    if provider == "openai":
        from src.core.openai_provider import OpenAIProvider

        return OpenAIProvider(model_name=model, api_key=os.getenv("OPENAI_API_KEY"))
    if provider in {"google", "gemini"}:
        from src.core.gemini_provider import GeminiProvider

        gemini_model = model if model else "gemini-1.5-flash"
        return GeminiProvider(model_name=gemini_model, api_key=os.getenv("GEMINI_API_KEY"))
    if provider == "local":
        from src.core.local_provider import LocalProvider

        model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
        max_tokens = int(os.getenv("LOCAL_MAX_TOKENS", "192"))
        return LocalProvider(model_path=model_path, max_tokens=max_tokens)
    if provider == "mock":
        from src.core.mock_provider import MockProvider

        return MockProvider(model_name=model or "mock-edu")

    raise ValueError(f"Unsupported DEFAULT_PROVIDER={provider}")
