# Lab Scoring Rubric: Chatbot vs ReAct Agent

This document outlines the grading criteria for Lab 3. The goal is to demonstrate deep understanding of agentic reasoning, robust monitoring, and iterative improvement.

## 1. Group Score (45 Points Base + 15 Points Bonus = Max 60)

This score reflects the collective output of the team. The total group score (Base + Bonus) is capped at **60 points**.

| Category | Description | Points |
| :--- | :--- | ---: |
| **Chatbot Baseline** | Implementation of a clean, minimal chatbot baseline. | 2 |
| **Agent v1 (Working)** | Successful implementation of the ReAct loop with 2+ tools. | 7 |
| **Agent v2 (Improved)** | Improved agent logic addressing failures identified in v1. | 7 |
| **Tool Design Evolution** | Clear documentation of tool spec progression. | 4 |
| **Trace Quality** | Documentation of both successful and failed traces. | 9 |
| **Evaluation & Analysis** | Data-driven comparison of Chatbot vs Agent. | 7 |
| **Flowchart & Insight** | Visual logic diagram and group learning points. | 5 |
| **Code Quality** | Clean code, modularity, and telemetry integration. | 4 |

> **Tip**
> Group submissions should use `report/group_report/TEMPLATE_GROUP_REPORT.md` as the structure for the final report.

### Group Bonus Points (Max +15)

Bonus points can be earned to reach the 60-point cap or to compensate for missed base points:

| Bonus Category | Description | Points |
| :--- | :--- | ---: |
| **Extra Monitoring** | Adding complex industry metrics such as cost and token ratio. | +3 |
| **Extra Tools** | Implementing advanced/additional tools. | +2 |
| **Failure Handling** | Sophisticated retry logic or guardrails. | +3 |
| **Live System Demo** | Successful live demonstration to the instructor. | +5 |
| **Ablation Experiments** | Comparison of prompt/tool variations. | +2 |

---

## 2. Individual Score (40 Points)

To earn the full 40 points, each student must submit an individual report in `report/individual_reports/`.

| Component | Rubric / Requirement | Points |
| :--- | :--- | ---: |
| **I. Technical Contribution** | List of specific code modules, tools, or tests implemented. Evidence of code quality and clarity. | 15 |
| **II. Debugging Case Study** | Detailed analysis of at least one failure and how it was resolved using telemetry/logs. | 10 |
| **III. Personal Insights** | Deep reflection on the differences between LLM chatbots and ReAct agents based on lab results. | 10 |
| **IV. Future Improvements** | Proposal for scaling this agent to a production-level RAG or multi-agent system. | 5 |

---

## Total Score Calculation

Final grade:

```text
Total = MIN(60, Group Base + Group Bonus) + Individual Score
```

Maximum score:

```text
60 group points + 40 individual points = 100 points
```

> **Important**
> Scoring transparency: the individual report template is in `report/individual_reports/TEMPLATE_INDIVIDUAL_REPORT.md`.

> **Important**
> Accountability: the 40% individual weighting ensures every student contributes significantly and understands the agent loop.

> **Important**
> Fail early, learn fast: quality failure analysis is valued as much as the final working code. A well-documented failure trace is worth more than a "perfect" system with no explanation.
