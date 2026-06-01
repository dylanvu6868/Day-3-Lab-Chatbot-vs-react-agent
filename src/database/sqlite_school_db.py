import os
import re
import sqlite3
from typing import Iterable, List, Tuple


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SQL_FILE = os.path.join(ROOT_DIR, "database", "database_mysql.sql")
SQLITE_DB_FILE = os.path.join(ROOT_DIR, "database", "school.db")


def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(SQLITE_DB_FILE), exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_bootstrap() -> None:
    conn = get_connection()
    try:
        if _has_data(conn):
            return
        _create_schema(conn)
        _load_data_from_mysql_dump(conn)
        conn.commit()
    finally:
        conn.close()


def _has_data(conn: sqlite3.Connection) -> bool:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='Students'"
    )
    if not cursor.fetchone():
        return False
    cursor.execute("SELECT COUNT(1) AS c FROM Students")
    return int(cursor.fetchone()[0]) > 0


def _create_schema(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.executescript(
        """
        DROP TABLE IF EXISTS Exams;
        DROP TABLE IF EXISTS Schedules;
        DROP TABLE IF EXISTS Students;
        DROP TABLE IF EXISTS Subjects;

        CREATE TABLE Students (
            student_id TEXT PRIMARY KEY,
            full_name TEXT
        );

        CREATE TABLE Subjects (
            subject_id INTEGER PRIMARY KEY,
            subject_name TEXT
        );

        CREATE TABLE Schedules (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            subject_id INTEGER,
            day_of_week INTEGER,
            start_time TEXT,
            room TEXT,
            FOREIGN KEY (student_id) REFERENCES Students(student_id),
            FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id)
        );

        CREATE TABLE Exams (
            exam_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            subject_id INTEGER,
            exam_date TEXT,
            start_time TEXT,
            room TEXT,
            FOREIGN KEY (student_id) REFERENCES Students(student_id),
            FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id)
        );
        """
    )


def _load_data_from_mysql_dump(conn: sqlite3.Connection) -> None:
    if not os.path.exists(SQL_FILE):
        raise FileNotFoundError(f"SQL dump not found: {SQL_FILE}")

    with open(SQL_FILE, "r", encoding="utf-8") as f:
        sql_text = f.read()

    _insert_subjects(conn, _extract_values_block(sql_text, "Subjects", first=True))
    _insert_students(conn, _extract_values_block(sql_text, "Students", first=True))
    _insert_schedules(conn, _extract_values_block(sql_text, "Schedules", first=True))
    _insert_exams(conn, _extract_values_block(sql_text, "Exams", first=True))


def _extract_values_block(sql_text: str, table_name: str, first: bool = True) -> str:
    pattern = re.compile(
        rf"INSERT\s+INTO\s+{table_name}\s*\([^;]*?\)\s*VALUES\s*(.*?);",
        flags=re.IGNORECASE | re.DOTALL,
    )
    matches = pattern.findall(sql_text)
    if not matches:
        return ""
    return matches[0] if first else matches[-1]


def _parse_rows(values_block: str) -> List[Tuple[str, ...]]:
    rows: List[Tuple[str, ...]] = []
    if not values_block:
        return rows

    current = []
    token = ""
    depth = 0
    in_string = False
    i = 0
    while i < len(values_block):
        ch = values_block[i]
        if ch == "'":
            in_string = not in_string
            token += ch
        elif not in_string and ch == "(":
            depth += 1
            if depth == 1:
                current = []
                token = ""
            else:
                token += ch
        elif not in_string and ch == ")":
            depth -= 1
            if depth == 0:
                if token.strip():
                    current.append(token.strip())
                rows.append(tuple(_clean_value(x) for x in current))
                token = ""
            else:
                token += ch
        elif not in_string and ch == "," and depth == 1:
            current.append(token.strip())
            token = ""
        else:
            token += ch
        i += 1
    return rows


def _clean_value(v: str) -> str:
    v = v.strip()
    if v.upper() == "NULL":
        return ""
    if len(v) >= 2 and v[0] == "'" and v[-1] == "'":
        return v[1:-1].replace("\\'", "'")
    return v


def _insert_subjects(conn: sqlite3.Connection, values_block: str) -> None:
    rows = _parse_rows(values_block)
    unique_rows = []
    seen = set()
    for row in rows:
        if len(row) < 2:
            continue
        key = int(row[0])
        if key in seen:
            continue
        seen.add(key)
        unique_rows.append((int(row[0]), row[1]))
    conn.executemany(
        "INSERT INTO Subjects(subject_id, subject_name) VALUES (?, ?)", unique_rows
    )


def _insert_students(conn: sqlite3.Connection, values_block: str) -> None:
    rows = _parse_rows(values_block)
    prepared = [(row[0], row[1]) for row in rows if len(row) >= 2]
    conn.executemany(
        "INSERT INTO Students(student_id, full_name) VALUES (?, ?)", prepared
    )


def _insert_schedules(conn: sqlite3.Connection, values_block: str) -> None:
    rows = _parse_rows(values_block)
    prepared = []
    for row in rows:
        if len(row) < 5:
            continue
        prepared.append((row[0], int(row[1]), int(row[2]), row[3], row[4]))
    conn.executemany(
        "INSERT INTO Schedules(student_id, subject_id, day_of_week, start_time, room) VALUES (?, ?, ?, ?, ?)",
        prepared,
    )


def _insert_exams(conn: sqlite3.Connection, values_block: str) -> None:
    rows = _parse_rows(values_block)
    prepared = []
    for row in rows:
        if len(row) < 5:
            continue
        prepared.append((row[0], int(row[1]), row[2], row[3], row[4]))
    conn.executemany(
        "INSERT INTO Exams(student_id, subject_id, exam_date, start_time, room) VALUES (?, ?, ?, ?, ?)",
        prepared,
    )
