from src.core.provider_factory import build_provider
from src.telemetry.metrics import tracker


def main() -> None:
    llm = build_provider()
    print("Chatbot baseline (go 'exit' de thoat)")
    while True:
        user_input = input("User: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        result = llm.generate(user_input)
        tracker.track_request(
            provider=result.get("provider", "unknown"),
            model=llm.model_name,
            usage=result.get("usage", {}),
            latency_ms=result.get("latency_ms", 0),
        )
        print(f"Assistant: {result.get('content', '').strip()}")


if __name__ == "__main__":
    main()
