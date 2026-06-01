from src.agent.agent import ReActAgent
from src.core.provider_factory import build_provider
from src.tools.school_db_tools import get_tools


def main() -> None:
    llm = build_provider()
    agent = ReActAgent(llm=llm, tools=get_tools(), max_steps=5)

    print("ReAct Agent (go 'exit' de thoat)")
    while True:
        user_input = input("User: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        answer = agent.run(user_input)
        print(f"Assistant: {answer}")


if __name__ == "__main__":
    main()
