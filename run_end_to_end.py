import os
from dataclasses import dataclass

from src.agent.agent import ReActAgent
from src.core.mock_provider import MockProvider
from src.database.sqlite_school_db import ensure_bootstrap, get_connection
from src.telemetry.metrics import tracker
from src.tools.school_db_tools import get_tools


@dataclass
class EvalCase:
    name: str
    query: str
    expected_terms: list[str]


def _first_exam_cases(limit: int = 3) -> list[EvalCase]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT e.student_id, s.subject_name
            FROM Exams e
            JOIN Subjects s ON s.subject_id = e.subject_id
            ORDER BY e.exam_id
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    return [
        EvalCase(
            name=f"exam_room_{idx}",
            query=(
                f"Cho minh lich thi mon {row['subject_name']} cua MSSV "
                f"{row['student_id']} va phong thi o dau?"
            ),
            expected_terms=["thi luc", "phong", "toa"],
        )
        for idx, row in enumerate(rows, start=1)
    ]


def _build_test_cases() -> list[EvalCase]:
    return [
        *_first_exam_cases(),
        EvalCase(
            name="student_list_subject",
            query="Cho toi danh sach cac sinh vien hoc mon Hoc may",
            expected_terms=["2a2026", "sinhvien"],
        ),
        EvalCase(
            name="student_list_range",
            query="Cho toi danh sach sinh vien tu 101 den 105",
            expected_terms=["2a202600101", "2a202600105"],
        ),
        EvalCase(
            name="student_profile",
            query="Thong tin sinh vien 2A202600632",
            expected_terms=["sinhvien 632", "2a202600632"],
        ),
    ]


def run_chatbot_baseline(llm: MockProvider, query: str) -> str:
    return llm.generate(query).get("content", "")


def is_success(answer: str, expected_terms: list[str]) -> bool:
    low = answer.lower()
    return all(term.lower() in low for term in expected_terms)


def _metric_summary() -> dict[str, float]:
    metrics = tracker.session_metrics
    if not metrics:
        return {
            "requests": 0,
            "total_tokens": 0,
            "avg_tokens": 0,
            "avg_latency_ms": 0,
            "total_cost_estimate": 0,
        }

    total_tokens = sum(m.get("total_tokens", 0) for m in metrics)
    total_latency = sum(m.get("latency_ms", 0) for m in metrics)
    total_cost = sum(m.get("cost_estimate", 0) for m in metrics)
    total_ratio = sum(m.get("completion_to_prompt_ratio", 0) for m in metrics)
    return {
        "requests": len(metrics),
        "total_tokens": total_tokens,
        "avg_tokens": round(total_tokens / len(metrics), 2),
        "avg_completion_to_prompt_ratio": round(total_ratio / len(metrics), 4),
        "avg_latency_ms": round(total_latency / len(metrics), 2),
        "total_cost_estimate": round(total_cost, 6),
    }


def main() -> None:
    ensure_bootstrap()
    tracker.session_metrics.clear()

    llm = MockProvider()
    agent = ReActAgent(llm=llm, tools=get_tools(), max_steps=5)
    test_cases = _build_test_cases()

    rows = []
    for case in test_cases:
        before_history = len(agent.history)
        chatbot_answer = run_chatbot_baseline(llm, case.query)
        agent_answer = agent.run(case.query)
        trace = agent.history[before_history:]
        rows.append(
            {
                "case": case,
                "chatbot": chatbot_answer,
                "agent": agent_answer,
                "chatbot_success": is_success(chatbot_answer, case.expected_terms),
                "agent_success": is_success(agent_answer, case.expected_terms),
                "trace_steps": len(trace),
            }
        )

    chatbot_success = sum(1 for row in rows if row["chatbot_success"])
    agent_success = sum(1 for row in rows if row["agent_success"])
    metrics = _metric_summary()

    report_lines = [
        "# End-to-End Run Report",
        "",
        "## Summary",
        "",
        f"- Total test cases: {len(test_cases)}",
        f"- Chatbot success: {chatbot_success}/{len(test_cases)}",
        f"- ReAct agent success: {agent_success}/{len(test_cases)}",
        f"- LLM requests tracked: {metrics['requests']}",
        f"- Total tokens estimated: {metrics['total_tokens']}",
        f"- Average tokens/request: {metrics['avg_tokens']}",
        f"- Average completion/prompt ratio: {metrics['avg_completion_to_prompt_ratio']}",
        f"- Average latency/request: {metrics['avg_latency_ms']} ms",
        f"- Total cost estimate: ${metrics['total_cost_estimate']}",
        "",
        "## Case Results",
        "",
        "| Case | Chatbot | Agent | Agent Steps |",
        "| :--- | :---: | :---: | ---: |",
    ]

    for row in rows:
        report_lines.append(
            "| {name} | {cb} | {ag} | {steps} |".format(
                name=row["case"].name,
                cb="PASS" if row["chatbot_success"] else "FAIL",
                ag="PASS" if row["agent_success"] else "FAIL",
                steps=row["trace_steps"],
            )
        )

    report_lines.extend(["", "## Sample Outputs", ""])

    for idx, row in enumerate(rows, start=1):
        report_lines.extend(
            [
                f"### Case {idx}: {row['case'].name}",
                f"- Query: {row['case'].query}",
                f"- Expected terms: {', '.join(row['case'].expected_terms)}",
                f"- Chatbot: {row['chatbot']}",
                f"- Agent: {row['agent']}",
                "",
            ]
        )

    os.makedirs("report", exist_ok=True)
    with open("report/END_TO_END_REPORT.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print("Da chay xong end-to-end. Bao cao: report/END_TO_END_REPORT.md")


if __name__ == "__main__":
    main()
