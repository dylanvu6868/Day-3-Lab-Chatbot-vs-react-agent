# Prompt Guardrails for the ReAct Agent

File implemented: `src/agent/agent.py`

The system prompt is written in Vietnamese to make the agent easier to inspect during a Vietnamese classroom demo. The prompt is designed to prevent hallucination, uncontrolled tool use, and irrelevant answers.

## 1. Scope Control

The agent is restricted to school-service questions:

- students
- schedules
- exams
- subjects
- classrooms
- room locations

If a user asks outside this scope, the agent should answer briefly:

```text
Mình chỉ hỗ trợ tra cứu thông tin học vụ trong hệ thống này.
```

## 2. Tool-First Rule

For any question related to school data, the agent must call a tool before answering.

Examples:

- Student list -> `list_students`
- Student profile -> `get_student_profile`
- Exam lookup -> `get_exam_info`
- Exam room location -> `search_room_location`
- Schedule lookup -> `get_student_schedule` or `get_daily_schedule`

This prevents the model from answering from memory.

## 3. Anti-Hallucination Rules

The prompt explicitly says:

- Do not invent data.
- Do not add rows that are not in the observation.
- If a tool says "not found", answer "not found".
- If a list is returned, copy it faithfully.
- Do not claim that more records exist unless the observation says so.

## 4. Missing-Information Rule

If required parameters are missing, the agent should ask for the missing field.

Examples:

- Exam lookup without `student_id` -> ask for MSSV.
- Exam lookup without `subject_name` -> ask for subject name.
- Ambiguous schedule query -> ask for day, room, or student ID when needed.

## 5. Security and Privacy Rules

The prompt blocks disclosure of:

- system prompt
- API keys
- environment variables
- internal logs
- sensitive implementation details

The agent should only return data that comes from a tool observation.

## 6. Output Format

The model must use:

```text
Thought: <short Vietnamese next-step summary>
Action: tool_name({"arg":"value"})
Observation: <filled by the environment>
Final Answer: <Vietnamese answer for user>
```

The app extracts `Final Answer` and shows only the user-facing answer in the chat UI.

## 7. Recovery Rules

If a tool call fails:

- Bad JSON -> `Tool argument parse error`
- Wrong/missing parameter -> `Tool argument error`
- Unknown tool -> `Tool <name> not found`
- Tool exception -> `Tool execution error`

The next prompt tells the model to fix the tool arguments or ask the user for missing information instead of making up an answer.
