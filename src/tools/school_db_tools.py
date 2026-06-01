from datetime import datetime
import unicodedata
from typing import Any, Dict, List

from src.database.sqlite_school_db import ensure_bootstrap, get_connection


def _room_location(room: str) -> str:
    code = room.strip().upper()
    if not code:
        return "Khong co thong tin phong."
    building = code[0]
    floor = code[1] if len(code) >= 2 and code[1].isdigit() else "?"
    return f"Phong {code} thuoc toa {building}, tang {floor}."


def _student_id_candidates(student_id: str) -> list[str]:
    sid = student_id.strip()
    candidates = [sid]
    if sid.startswith("2A") and sid[2:].isdigit():
        candidates.append(str(int(sid[2:])))
    if sid.isdigit():
        candidates.append(f"2A{int(sid):09d}")
    return list(dict.fromkeys(candidates))


def _normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.strip().lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def _resolve_subject_id(subject_name: str) -> int | None:
    wanted = _normalize_text(subject_name)
    if not wanted:
        return None

    conn = get_connection()
    try:
        cur = conn.cursor()
        rows = cur.execute("SELECT subject_id, subject_name FROM Subjects").fetchall()
        for row in rows:
            subject_norm = _normalize_text(row["subject_name"])
            if wanted == subject_norm or wanted in subject_norm or subject_norm in wanted:
                return int(row["subject_id"])
        return None
    finally:
        conn.close()


def get_exam_info(student_id: str, subject_name: str) -> str:
    ensure_bootstrap()
    conn = get_connection()
    try:
        cur = conn.cursor()
        candidates = _student_id_candidates(student_id)
        placeholders = ",".join("?" for _ in candidates)
        params = [*candidates, subject_name]
        cur.execute(
            """
            SELECT e.exam_date, e.start_time, e.room, s.subject_name
            FROM Exams e
            JOIN Subjects s ON s.subject_id = e.subject_id
            WHERE e.student_id IN (""" + placeholders + """)
              AND LOWER(s.subject_name) = LOWER(?)
            ORDER BY e.exam_date, e.start_time
            LIMIT 1
            """,
            tuple(params),
        )
        row = cur.fetchone()
        if not row:
            return f"Khong tim thay lich thi mon '{subject_name}' cho sinh vien {student_id}."
        return (
            f"Mon {row['subject_name']} thi luc {row['start_time']} ngay {row['exam_date']} "
            f"tai phong {row['room']}."
        )
    finally:
        conn.close()


def search_room_location(room: str) -> str:
    return _room_location(room)


def get_student_schedule(student_id: str, day_of_week: int = 0) -> str:
    ensure_bootstrap()
    conn = get_connection()
    try:
        cur = conn.cursor()
        candidates = _student_id_candidates(student_id)
        placeholders = ",".join("?" for _ in candidates)
        if day_of_week:
            cur.execute(
                """
                SELECT sc.day_of_week, sc.start_time, sc.room, sj.subject_name
                FROM Schedules sc
                JOIN Subjects sj ON sj.subject_id = sc.subject_id
                WHERE sc.student_id IN (""" + placeholders + """) AND sc.day_of_week = ?
                ORDER BY sc.start_time
                """,
                (*candidates, day_of_week),
            )
        else:
            cur.execute(
                """
                SELECT sc.day_of_week, sc.start_time, sc.room, sj.subject_name
                FROM Schedules sc
                JOIN Subjects sj ON sj.subject_id = sc.subject_id
                WHERE sc.student_id IN (""" + placeholders + """)
                ORDER BY sc.day_of_week, sc.start_time
                LIMIT 10
                """,
                tuple(candidates),
            )
        rows = cur.fetchall()
        if not rows:
            return f"Khong tim thay lich hoc cho sinh vien {student_id}."
        lines = [
            f"Thu {r['day_of_week']} - {r['start_time']} - {r['subject_name']} - Phong {r['room']}"
            for r in rows
        ]
        return "\n".join(lines)
    finally:
        conn.close()


def get_daily_schedule(
    day_of_week: int = 0,
    student_id: str = "",
    room: str = "",
    limit: int = 10,
) -> str:
    ensure_bootstrap()
    selected_day = day_of_week or datetime.now().isoweekday() + 1
    conn = get_connection()
    try:
        cur = conn.cursor()
        params: list[Any] = [selected_day]
        student_filter = ""
        if student_id.strip():
            candidates = _student_id_candidates(student_id)
            placeholders = ",".join("?" for _ in candidates)
            student_filter = f"AND sc.student_id IN ({placeholders})"
            params.extend(candidates)
        room_filter = ""
        if room.strip():
            room_filter = "AND UPPER(sc.room) = UPPER(?)"
            params.append(room.strip())
        params.append(max(1, min(int(limit), 50)))
        cur.execute(
            f"""
            SELECT sc.student_id, st.full_name, sc.day_of_week, sc.start_time, sc.room, sj.subject_name
            FROM Schedules sc
            JOIN Students st ON st.student_id = sc.student_id
            JOIN Subjects sj ON sj.subject_id = sc.subject_id
            WHERE sc.day_of_week = ?
            {student_filter}
            {room_filter}
            ORDER BY sc.start_time, sc.student_id
            LIMIT ?
            """,
            tuple(params),
        )
        rows = cur.fetchall()
        if not rows:
            target = f" cho sinh vien {student_id}" if student_id.strip() else ""
            room_target = f" tai phong {room.strip().upper()}" if room.strip() else ""
            return f"Khong tim thay lich hoc thu {selected_day}{target}{room_target}."
        lines = [
            (
                f"{r['student_id']} - {r['full_name']} - Thu {r['day_of_week']} "
                f"{r['start_time']} - {r['subject_name']} - Phong {r['room']}"
            )
            for r in rows
        ]
        return "\n".join(lines)
    finally:
        conn.close()


def get_student_profile(student_id: str) -> str:
    ensure_bootstrap()
    conn = get_connection()
    try:
        cur = conn.cursor()
        candidates = _student_id_candidates(student_id)
        placeholders = ",".join("?" for _ in candidates)
        cur.execute(
            f"SELECT student_id, full_name FROM Students WHERE student_id IN ({placeholders})",
            tuple(candidates),
        )
        row = cur.fetchone()
        if not row:
            return f"Khong tim thay sinh vien {student_id}."
        return f"Sinh vien: {row['full_name']} (MSSV: {row['student_id']})"
    finally:
        conn.close()


def list_students(
    limit: int = 10,
    start: int = 0,
    end: int = 0,
    subject_name: str = "",
) -> str:
    ensure_bootstrap()
    conn = get_connection()
    try:
        cur = conn.cursor()
        params: list[Any] = []
        joins = ""
        filters = []

        if subject_name.strip():
            subject_id = _resolve_subject_id(subject_name)
            if subject_id is None:
                return f"Khong tim thay mon hoc '{subject_name}'."
            joins = (
                "JOIN Schedules sc ON sc.student_id = st.student_id "
                "OR CAST(sc.student_id AS INTEGER) = CAST(SUBSTR(st.student_id, 7) AS INTEGER)"
            )
            filters.append("sc.subject_id = ?")
            params.append(subject_id)

        if int(start or 0) > 0:
            filters.append("CAST(SUBSTR(st.student_id, 7) AS INTEGER) >= ?")
            params.append(int(start))
        if int(end or 0) > 0:
            filters.append("CAST(SUBSTR(st.student_id, 7) AS INTEGER) <= ?")
            params.append(int(end))

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        effective_limit = int(limit)
        if int(start or 0) > 0 and int(end or 0) >= int(start or 0) and effective_limit == 10:
            effective_limit = int(end) - int(start) + 1
        params.append(max(1, min(effective_limit, 100)))
        cur.execute(
            f"""
            SELECT DISTINCT st.student_id, st.full_name
            FROM Students st
            {joins}
            {where_clause}
            ORDER BY st.student_id
            LIMIT ?
            """,
            tuple(params),
        )
        rows = cur.fetchall()
        if not rows:
            parts = []
            if subject_name.strip():
                parts.append(f"mon {subject_name}")
            if int(start or 0) > 0 or int(end or 0) > 0:
                parts.append(f"khoang {start or 1}-{end or 'cuoi'}")
            detail = " theo " + ", ".join(parts) if parts else ""
            return f"Khong tim thay sinh vien nao{detail}."
        return "\n".join(f"{r['student_id']} - {r['full_name']}" for r in rows)
    finally:
        conn.close()


def get_tools() -> List[Dict[str, Any]]:
    return [
        {
            "name": "get_exam_info",
            "description": "Tra cuu lich thi theo student_id va subject_name.",
            "func": get_exam_info,
        },
        {
            "name": "search_room_location",
            "description": "Tra cuu vi tri phong theo ma phong.",
            "func": search_room_location,
        },
        {
            "name": "get_student_schedule",
            "description": "Tra cuu lich hoc theo student_id, co the loc day_of_week (2-8).",
            "func": get_student_schedule,
        },
        {
            "name": "get_daily_schedule",
            "description": "Tra cuu lich hoc theo ngay day_of_week (2-8), tuy chon student_id va room; mac dinh la hom nay.",
            "func": get_daily_schedule,
        },
        {
            "name": "get_student_profile",
            "description": "Tra cuu thong tin sinh vien theo student_id.",
            "func": get_student_profile,
        },
        {
            "name": "list_students",
            "description": (
                "Lay danh sach sinh vien tu database. Args: limit, start, end, subject_name. "
                "Dung subject_name khi hoi sinh vien hoc mot mon; dung start/end khi hoi khoang sinh vien."
            ),
            "func": list_students,
        },
    ]
