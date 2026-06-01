# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Vu Hai Duong
- **Student ID**: 2A202600632
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

### Modules implemented or improved

- `src/agent/agent.py`
- `src/tools/school_db_tools.py`
- `src/database/sqlite_school_db.py`
- `src/core/mock_provider.py`
- `src/core/openai_provider.py`
- `src/core/gemini_provider.py`
- `src/telemetry/logger.py`
- `src/telemetry/metrics.py`
- `web_chatbot.py`
- `frontend/index.html`
- `frontend/styles.css`
- `frontend/app.js`
- `tests/test_agent.py`
- `run_end_to_end.py`

### Code highlights

I completed the ReAct loop in `src/agent/agent.py`:

- Generate an LLM response with a system prompt.
- Detect `Final Answer`.
- Parse `Action: tool({...})`.
- Execute the matching Python tool.
- Append `Observation` and continue the loop.
- Stop after `max_steps`.

I also strengthened the parser:

- Supports JSON arguments.
- Supports simple `key=value` arguments.
- Handles nested parentheses inside quoted strings.
- Converts parse errors into tool observations instead of crashing.

I expanded the school database tool layer:

- `get_exam_info`
- `search_room_location`
- `get_student_schedule`
- `get_daily_schedule`
- `get_student_profile`
- `list_students`

The most important data fix was in `list_students`: the SQL dump stores schedule IDs as numbers while the student table stores IDs as `2A2026...`, so I added a join by numeric suffix.

### Testing contribution

I added `tests/test_agent.py` to cover:

- JSON argument parsing.
- `key=value` argument parsing.
- Action parsing with parentheses inside strings.
- Multi-step ReAct exam lookup.
- Controlled tool parse failure.
- Student list filtering by range and subject.

---

## II. Debugging Case Study (10 Points)

### Problem description

The agent initially failed on student list questions:

```text
Cho toi danh sach cac sinh vien hoc mon Hoc may
```

The tool returned:

```text
Khong tim thay sinh vien nao theo mon Hoc may.
```

This was incorrect because the SQL dump contains schedules for the subject `Hoc may`.

### Log source

The structured log showed:

```text
AGENT_STEP -> Action: list_students({"subject_name":"Hoc may","limit":10})
TOOL_CALL -> list_students subject_name=Hoc may
TOOL_RESULT -> Khong tim thay sinh vien nao theo mon Hoc may.
```

This proved the LLM chose the right tool. The bug was inside the tool/database layer, not the LLM.

### Diagnosis

The database has inconsistent ID formats:

- `Students.student_id`: `2A202600001`
- `Schedules.student_id`: `1`

The first implementation joined the tables directly:

```sql
Schedules.student_id = Students.student_id
```

That join cannot match `1` with `2A202600001`, so subject-filtered queries returned zero rows.

### Solution

I changed the join so the numeric suffix of `Students.student_id` can match `Schedules.student_id`:

```sql
CAST(sc.student_id AS INTEGER) = CAST(SUBSTR(st.student_id, 7) AS INTEGER)
```

I then added regression tests:

```python
by_subject = list_students(subject_name="Hoc may", limit=5)
assert "2A2026" in by_subject
assert "Khong tim thay" not in by_subject
```

### Result

The query now returns real student rows from SQLite, and the test suite passes.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning

A direct chatbot answers in one pass. In the upgraded baseline, it can also use direct tool lookup through a simple intent router. That is fast and works well for fixed patterns, but it is less transparent than ReAct because it does not expose a step-by-step `Thought -> Action -> Observation` trace.

For example, "exam schedule and room location" is naturally multi-step:

1. Find exam info.
2. Extract the room.
3. Find room location.
4. Combine both observations.

The `Thought` block makes this plan explicit and debuggable, while the direct chatbot hides that routing inside code.

### 2. Reliability

The agent can perform worse than a chatbot when:

- The tool schema is unclear.
- The parser is fragile.
- The database schema has hidden inconsistencies.
- The model calls the right tool but with wrong arguments.

This happened in the subject-filtered student list bug. The ReAct trace helped isolate the problem quickly.

### 3. Observation

Observation is the main reliability advantage. The model does not need to guess. It can read the exact database result and use it in the next step.

The strongest example is room lookup:

```text
Observation: ... tai phong D401.
Action: search_room_location({"room":"D401"})
```

The second action depends directly on the first observation.

---

## IV. Future Improvements (5 Points)

Scalability:

- Move tool execution to async functions.
- Add request-level IDs for tracing concurrent users.
- Add a tool registry with typed schemas.

Safety:

- Add authentication before returning personal student data.
- Add role-based access control for teacher/admin/student views.
- Mask sensitive fields in logs.

Performance:

- Cache common queries such as room location and subject list.
- Add a vector/RAG layer for policy documents and academic regulations.
- Use a smaller local model for cheap routing and a stronger model only for hard queries.

Production direction:

- Convert the current ReAct loop into a graph-based workflow when branching grows.
- Add monitoring dashboards for success rate, parser error rate, latency, loop count, and cost.
