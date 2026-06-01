from typing import Dict, Any


EXAM_DB = {
    ("10A", "toan"): {"date": "20/06", "time": "14:00", "room": "C205"},
    ("10A", "van"): {"date": "21/06", "time": "08:00", "room": "B101"},
}

ROOM_DB = {
    "C205": "Phong C205 thuoc Toa C, tang 2, gan cau thang bo.",
    "B101": "Phong B101 thuoc Toa B, tang 1, doi dien phong hanh chinh.",
}


def get_exam_info(class_name: str, subject: str) -> str:
    key = (class_name.strip().upper(), subject.strip().lower())
    data = EXAM_DB.get(key)
    if not data:
        return f"Khong tim thay lich thi cho lop {class_name}, mon {subject}."
    return f"Ngay thi {data['date']}, {data['time']}, phong {data['room']}."


def search_room_location(room: str) -> str:
    room_code = room.strip().upper()
    return ROOM_DB.get(room_code, f"Khong tim thay vi tri phong {room_code}.")


def get_student_score(student_id: str, term: str) -> str:
    return f"Diem hoc ky {term} cua sinh vien {student_id}: Toan 8.5, Van 8.0, Anh 8.8."


def get_schedule(class_name: str, week: str) -> str:
    return f"Lich hoc tuan {week} cua lop {class_name}: Toan (T2), Van (T3), Anh (T5)."


def get_announcements(scope: str = "all") -> str:
    return f"Thong bao {scope}: Dang ky hoc phan mo tu 01/07 den 05/07; su kien huong nghiep 03/07."


def get_tools() -> list[Dict[str, Any]]:
    return [
        {
            "name": "get_exam_info",
            "description": "Tra cuu lich thi theo class_name va subject.",
            "func": get_exam_info,
        },
        {
            "name": "search_room_location",
            "description": "Tra cuu vi tri phong theo ma phong room.",
            "func": search_room_location,
        },
        {
            "name": "get_student_score",
            "description": "Lay diem hoc phan cua sinh vien theo student_id va term.",
            "func": get_student_score,
        },
        {
            "name": "get_schedule",
            "description": "Tra cuu lich hoc theo class_name va week.",
            "func": get_schedule,
        },
        {
            "name": "get_announcements",
            "description": "Lay thong bao hoc vu va su kien theo pham vi scope.",
            "func": get_announcements,
        },
    ]
