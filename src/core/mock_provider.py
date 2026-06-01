import re
import time
import unicodedata
from typing import Any, Dict, Generator, Optional

from src.core.llm_provider import LLMProvider
from src.tools.school_db_tools import (
    get_daily_schedule,
    get_exam_info,
    get_student_profile,
    list_students,
    search_room_location,
)


class MockProvider(LLMProvider):
    def __init__(self, model_name: str = "mock-edu"):
        super().__init__(model_name=model_name, api_key=None)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start = time.time()
        if system_prompt and "ReAct" in system_prompt:
            content = self._agent_response(prompt)
        else:
            content = self._chatbot_response(prompt)
        latency_ms = int((time.time() - start) * 1000)
        usage = {
            "prompt_tokens": max(1, len(prompt) // 4),
            "completion_tokens": max(1, len(content) // 4),
            "total_tokens": max(2, (len(prompt) + len(content)) // 4),
        }
        return {
            "content": content,
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": "mock",
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        result = self.generate(prompt, system_prompt=system_prompt)
        yield result["content"]

    def _agent_response(self, prompt: str) -> str:
        if "Observation:" not in prompt:
            lowered = self._normalize_text(prompt)
            student_id = self._extract_student_id(prompt)
            if self._asks_for_student_list(lowered):
                args = []
                subject = self._extract_subject_only(prompt)
                start, end = self._extract_range(prompt)
                if subject:
                    args.append(f'"subject_name":"{subject}"')
                if start:
                    args.append(f'"start":{start}')
                if end:
                    args.append(f'"end":{end}')
                if not start and not end:
                    args.append('"limit":10')
                args_json = "{" + ",".join(args) + "}"
                return (
                    "Thought: Can doc danh sach sinh vien tu database.\n"
                    f"Action: list_students({args_json})"
                )
            if self._asks_for_schedule(lowered):
                room = self._extract_room(prompt)
                args = []
                if student_id:
                    args.append(f'"student_id":"{student_id}"')
                if room:
                    args.append(f'"room":"{room}"')
                args.append('"limit":10')
                args_json = "{" + ",".join(args) + "}"
                if student_id:
                    return (
                        "Thought: Can tra cuu lich hoc cua sinh vien trong database.\n"
                        f"Action: get_daily_schedule({args_json})"
                    )
                return (
                    "Thought: Can tra cuu lich hoc hom nay trong database.\n"
                    f"Action: get_daily_schedule({args_json})"
                )
            if student_id and self._asks_for_profile(lowered):
                return (
                    "Thought: Can tra cuu ho so sinh vien trong database.\n"
                    f'Action: get_student_profile({{"student_id":"{student_id}"}})'
                )

            student_id, subject = self._extract_student_subject(prompt)
            if student_id and subject:
                return (
                    "Thought: Can tim lich thi mon hoc truoc.\n"
                    f"Action: get_exam_info({{\"student_id\":\"{student_id}\",\"subject_name\":\"{subject}\"}})"
                )
            return (
                "Final Answer: Hay hoi theo dang: danh sach sinh vien, lich hoc hom nay, "
                "hoac lich thi mon <ten mon> cua MSSV <ma so>."
            )

        observations = self._extract_observations(prompt)
        last_obs = observations[-1] if observations else ""
        room_match = re.search(r"phong\s+([A-Z]\d+)", last_obs, flags=re.IGNORECASE)
        if room_match and "thuoc toa" not in last_obs.lower():
            room = room_match.group(1).upper()
            return (
                "Thought: Da co phong thi, can tim vi tri phong.\n"
                f"Action: search_room_location({{\"room\":\"{room}\"}})"
            )
        if observations and "thuoc toa" in last_obs.lower() and len(observations) >= 2:
            exam_obs = observations[-2]
            return f"Final Answer: {exam_obs} {last_obs}"
        return f"Final Answer: {last_obs}"

    def _chatbot_response(self, prompt: str) -> str:
        lowered = self._normalize_text(prompt)
        student_id = self._extract_student_id(prompt)

        if self._asks_for_student_list(lowered):
            subject = self._extract_subject_only(prompt)
            start, end = self._extract_range(prompt)
            return list_students(
                subject_name=subject or "",
                start=start or 0,
                end=end or 0,
                limit=10,
            )

        if self._asks_for_schedule(lowered):
            room = self._extract_room(prompt) or ""
            return get_daily_schedule(
                student_id=student_id or "",
                room=room,
                limit=10,
            )

        if student_id and self._asks_for_profile(lowered):
            return get_student_profile(student_id=student_id)

        student_id, subject = self._extract_student_subject(prompt)
        if student_id and subject:
            exam = get_exam_info(student_id=student_id, subject_name=subject)
            room_match = re.search(r"phong\s+([A-Z]\d+)", exam, flags=re.IGNORECASE)
            if room_match:
                location = search_room_location(room_match.group(1).upper())
                return f"{exam} {location}"
            return exam
        return "Toi la chatbot co ban. Hay cung cap MSSV va mon hoc."

    def _extract_observations(self, prompt: str) -> list[str]:
        matches = re.findall(
            r"Observation:\s*(.*?)(?=\nContinue\.|\nTiếp tục|\nTiep tuc|\n\nAssistant:|\Z)",
            prompt,
            flags=re.DOTALL,
        )
        return [match.strip() for match in matches if match.strip()]

    def _asks_for_student_list(self, lowered: str) -> bool:
        return "danh sach sinh vien" in lowered or (
            "danh sach" in lowered and "sinh vien" in lowered
        )

    def _asks_for_schedule(self, lowered: str) -> bool:
        schedule_words = ["lich hoc", "thoi khoa bieu"]
        return any(word in lowered for word in schedule_words)

    def _asks_for_profile(self, lowered: str) -> bool:
        profile_words = ["thong tin sinh vien", "ho so"]
        return any(word in lowered for word in profile_words)

    def _extract_student_id(self, text: str) -> Optional[str]:
        id_match = re.search(r"2A\d{9}|\b\d{1,4}\b", text)
        return id_match.group(0) if id_match else None

    def _extract_room(self, text: str) -> Optional[str]:
        room_match = re.search(r"\b[A-Z]\d{3}\b", text, flags=re.IGNORECASE)
        return room_match.group(0).upper() if room_match else None

    def _extract_range(self, text: str) -> tuple[Optional[int], Optional[int]]:
        normalized = self._normalize_text(text)
        match = re.search(r"\btu\s+(\d{1,4})\s+den\s+(\d{1,4})\b", normalized)
        if not match:
            return None, None
        return int(match.group(1)), int(match.group(2))

    def _extract_subject_only(self, text: str) -> Optional[str]:
        _, subject = self._extract_student_subject(text)
        return subject

    def _normalize_text(self, text: str) -> str:
        repaired = text
        try:
            repaired = text.encode("latin1").decode("utf-8")
        except UnicodeError:
            pass
        decomposed = unicodedata.normalize("NFD", repaired.lower())
        return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")

    def _extract_student_subject(self, text: str) -> tuple[Optional[str], Optional[str]]:
        aliases = {
            "big data": "Big Data",
            "lap trinh huong doi tuong": "Lập trình hướng đối tượng",
            "lập trình hướng đối tượng": "Lập trình hướng đối tượng",
            "lap trinh web": "Lập trình Web",
            "lập trình web": "Lập trình Web",
            "hoc may": "Học máy",
            "học máy": "Học máy",
            "lap trinh iot": "Lập trình IoT",
            "lập trình iot": "Lập trình IoT",
        }
        student_id = self._extract_student_id(text)
        lowered = self._normalize_text(text)
        subject = None
        for alias, canonical in aliases.items():
            if self._normalize_text(alias) in lowered:
                subject = canonical
                break
        return student_id, subject
