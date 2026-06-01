# Tool Call Examples and Trace Evidence

This file documents successful and failed traces used in the Lab 3 failure analysis.

## Success Trace 1: Exam Lookup + Room Location

```text
User: Cho minh lich thi mon Big Data cua MSSV 1 va phong thi o dau?

Thought: Can tim lich thi mon hoc truoc.
Action: get_exam_info({"student_id":"1","subject_name":"Big Data"})
Observation: Mon Big Data thi luc 11:00:00 ngay 2026-06-03 tai phong D401.

Thought: Da co phong thi, can tim vi tri phong.
Action: search_room_location({"room":"D401"})
Observation: Phong D401 thuoc toa D, tang 4.

Final Answer: Mon Big Data thi luc 11:00:00 ngay 2026-06-03 tai phong D401.
Phong D401 thuoc toa D, tang 4.
```

Why this is a strong ReAct trace:

- The agent does not answer from memory.
- It uses `get_exam_info` first, then uses the observed room code to call `search_room_location`.
- The final answer is grounded in both observations.

## Success Trace 2: Student Range Query

```text
User: Cho toi danh sach sinh vien tu 101 den 105

Thought: Can doc danh sach sinh vien tu database.
Action: list_students({"start":101,"end":105})
Observation:
2A202600101 - SinhVien 101
2A202600102 - SinhVien 102
2A202600103 - SinhVien 103
2A202600104 - SinhVien 104
2A202600105 - SinhVien 105

Final Answer:
2A202600101 - SinhVien 101
2A202600102 - SinhVien 102
2A202600103 - SinhVien 103
2A202600104 - SinhVien 104
2A202600105 - SinhVien 105
```

## Success Trace 3: Subject Filter Query

```text
User: Cho toi danh sach cac sinh vien hoc mon Hoc may

Thought: Can doc danh sach sinh vien tu database.
Action: list_students({"subject_name":"Hoc may","limit":10})
Observation:
2A202600001 - SinhVien 1
2A202600002 - SinhVien 2
2A202600003 - SinhVien 3
...

Final Answer: Danh sach sinh vien hoc mon Hoc may la ...
```

Implementation note:

- `list_students` resolves subject names by accent-insensitive matching.
- The tool joins `Schedules` to `Students` even though the SQL dump stores schedule student IDs as numeric suffixes while `Students.student_id` uses the `2A2026...` format.

## Failure Trace 1: Parser Error in Agent v1

```text
User: Tra cuu lich thi mon Math (A) cua MSSV 1

Agent v1 output:
Thought: Can tra cuu lich thi.
Action: get_exam_info({"student_id":"1","subject_name":"Math (A)"})

Bug:
The regex parser stopped at the first closing parenthesis inside the string "Math (A)".
Parsed args became incomplete JSON.
```

Root cause:

- Agent v1 used a greedy regex to parse `Action: tool(args)`.
- The parser did not track string boundaries or nested parentheses.

Fix:

- Agent v2 uses `_extract_action()` to scan the output character by character.
- It tracks parenthesis depth, quote state, and escape characters.
- Invalid JSON becomes a controlled observation: `Tool argument parse error`.

## Failure Trace 2: Data Model Mismatch

```text
User: Cho toi danh sach cac sinh vien hoc mon Hoc may

Observation in failed run:
Khong tim thay sinh vien nao theo mon Hoc may.
```

Root cause:

- `Students.student_id` uses values like `2A202600001`.
- `Schedules.student_id` in the dump uses numeric values like `1`, `2`, `3`.
- A direct join on `Students.student_id = Schedules.student_id` returned no rows.

Fix:

- `list_students` now joins using both exact ID and numeric suffix:
  `CAST(sc.student_id AS INTEGER) = CAST(SUBSTR(st.student_id, 7) AS INTEGER)`.

## Failure Trace 3: Provider/Model Availability

```text
Provider: Gemini
Model: gemini-1.5-flash
Error:
404 models/gemini-1.5-flash is not found for API version v1beta.
```

Fix:

- The system queried available Gemini models and switched the web default to a supported model at that time.
- The current web default was later changed to OpenAI `gpt-4o-mini` when requested.

## Guardrails Added

- `max_steps=5` prevents infinite loops.
- Unknown tools return `Tool <name> not found`.
- Bad JSON returns `Tool argument parse error`.
- Tool signature mismatch returns `Tool argument error`.
- Console telemetry is opt-in via `LOG_TO_CONSOLE=true`, while JSON logs remain in `logs/`.
