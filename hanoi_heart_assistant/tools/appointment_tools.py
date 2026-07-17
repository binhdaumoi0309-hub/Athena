"""Demo appointment adapter; replace these functions with the hospital scheduling API."""

import re
import os
import sqlite3
import uuid
from datetime import date, datetime
from pathlib import Path

DEPARTMENTS = {"tim_mach": "Tim mạch", "noi_tim_mach": "Nội tim mạch"}
DEMO_SLOTS = ("08:00", "09:30", "14:00", "15:30")

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PACKAGE_ROOT / "data" / "schedule.db"


def _parse_future_date(value: str) -> date | None:
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed >= date.today() else None


def list_appointment_slots(department: str, appointment_date: str) -> dict:
    """List demo appointment slots for a department and date in YYYY-MM-DD format."""
    parsed_date = _parse_future_date(appointment_date)
    if parsed_date is None:
        return {
            "status": "error",
            "message": "Ngày khám phải có dạng YYYY-MM-DD và không ở quá khứ.",
        }
    if department not in DEPARTMENTS:
        return {
            "status": "error",
            "message": "Chuyên khoa chưa được hỗ trợ.",
            "departments": DEPARTMENTS,
        }
    return {
        "status": "success",
        "source": "demo_slots_not_live",
        "department": DEPARTMENTS[department],
        "date": parsed_date.isoformat(),
        "slots": list(DEMO_SLOTS),
        "notice": "Khung giờ minh họa, chưa phản ánh lịch trống thực tế của bệnh viện.",
    }


def submit_appointment_request(
    full_name: str,
    phone: str,
    department: str,
    appointment_date: str,
    appointment_time: str,
    reason: str,
    doctor_name: str | None = None,
) -> dict:
    """Validate and submit an appointment request to Firestore, updating SQLite booked_count."""
    if len(full_name.strip()) < 2:
        return {"status": "error", "message": "Họ tên chưa hợp lệ."}
    if not re.fullmatch(r"(?:\+84|0)\d{9,10}", phone.replace(" ", "")):
        return {"status": "error", "message": "Số điện thoại chưa hợp lệ."}

    parsed_date = _parse_future_date(appointment_date)
    if parsed_date is None:
        return {
            "status": "error",
            "message": "Ngày khám phải có dạng YYYY-MM-DD và không ở quá khứ.",
        }

    try:
        hour = int(appointment_time.split(":")[0])
        shift = "morning" if hour < 12 else "afternoon"
    except (ValueError, IndexError):
        return {"status": "error", "message": "Giờ khám không hợp lệ (HH:MM)."}

    db_file = DB_PATH
    if not db_file.exists():
        return {"status": "error", "message": "Database lịch khám chưa được khởi tạo."}

    with sqlite3.connect(db_file) as con:
        con.row_factory = sqlite3.Row
        if doctor_name:
            query = """
                SELECT s.id, s.booked_count, s.value AS doctor_name, r.name AS room_name, i.facility
                FROM schedule_shifts s
                JOIN schedule_rooms r ON r.id = s.room_id
                JOIN schedule_areas a ON a.id = r.area_id
                JOIN schedule_days d ON d.id = s.day_id
                JOIN schedule_imports i ON i.id = a.import_id
                WHERE i.status = 'published'
                  AND d.work_date = ?
                  AND s.shift = ?
                  AND s.value = ?
            """
            row = con.execute(query, (parsed_date.isoformat(), shift, doctor_name)).fetchone()
        else:
            query = """
                SELECT s.id, s.booked_count, s.value AS doctor_name, r.name AS room_name, i.facility
                FROM schedule_shifts s
                JOIN schedule_rooms r ON r.id = s.room_id
                JOIN schedule_areas a ON a.id = r.area_id
                JOIN schedule_days d ON d.id = s.day_id
                JOIN schedule_imports i ON i.id = a.import_id
                WHERE i.status = 'published'
                  AND d.work_date = ?
                  AND s.shift = ?
                  AND s.state = 'working'
                ORDER BY s.booked_count ASC
            """
            row = con.execute(query, (parsed_date.isoformat(), shift)).fetchone()

    if not row:
        doctor_info = f" bác sĩ {doctor_name}" if doctor_name else ""
        return {
            "status": "error",
            "message": f"Không tìm thấy ca trực nào của{doctor_info} vào ngày {parsed_date.isoformat()} ca {'Sáng' if shift == 'morning' else 'Chiều'}."
        }

    shift_id = row["id"]
    active_doctor = row["doctor_name"]
    facility_id = f"Cơ sở {row['facility']}"
    current_booked = row["booked_count"] or 0

    try:
        max_bookings = int(os.getenv("MAX_BOOKINGS_PER_SHIFT", "6"))
    except ValueError:
        max_bookings = 6

    if current_booked >= max_bookings:
        return {
            "status": "error",
            "message": f"Ca trực của bác sĩ {active_doctor} đã đầy (tối đa {max_bookings} người)."
        }

    try:
        from hanoi_heart_assistant.tools.firebase_vector_tools import _firestore_client
        fs = _firestore_client()
        code = f"BVT-{uuid.uuid4().hex[:8].upper()}"
        app_id = str(uuid.uuid4())
        
        appointment_data = {
            "id": app_id,
            "code": code,
            "doctorId": active_doctor,
            "doctorName": active_doctor,
            "specialtyId": department,
            "specialty": DEPARTMENTS.get(department, department),
            "facilityId": facility_id,
            "facilityName": f"Bệnh viện Tim Hà Nội — {facility_id}",
            "date": parsed_date.isoformat(),
            "time": appointment_time,
            "status": "upcoming",
            "patientName": full_name.strip(),
            "patientPhone": phone.replace(" ", ""),
            "patientEmail": "",
            "patientDob": "",
            "patientGender": "",
            "symptoms": reason.strip(),
            "shift_id": shift_id,
            "created_at": datetime.utcnow().isoformat()
        }
        fs.collection("appointments").document(app_id).set(appointment_data)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Lỗi kết nối Firebase khi lưu đặt lịch: {str(e)}"
        }

    with sqlite3.connect(db_file) as con:
        con.execute("UPDATE schedule_shifts SET booked_count = booked_count + 1 WHERE id = ?", (shift_id,))

    return {
        "status": "success",
        "code": code,
        "appointment": appointment_data,
        "message": f"Đặt lịch thành công cho bệnh nhân {full_name} khám bác sĩ {active_doctor} lúc {appointment_time} ngày {parsed_date.isoformat()}."
    }
