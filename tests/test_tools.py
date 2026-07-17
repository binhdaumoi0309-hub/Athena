from datetime import date, timedelta

from hanoi_heart_assistant.tools.appointment_tools import (
    list_appointment_slots,
    submit_appointment_request,
)
from hanoi_heart_assistant.tools.medical_tools import search_medical_knowledge


def test_medical_search_flags_emergency() -> None:
    result = search_medical_knowledge("Tôi đau ngực dữ dội")
    assert result["emergency"] is True
    assert result["emergency_action"]


def test_rejects_past_appointment_date() -> None:
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    assert list_appointment_slots("tim_mach", yesterday)["status"] == "error"


def test_appointment_is_pending_not_confirmed(tmp_path, monkeypatch) -> None:
    temp_db = tmp_path / "schedule.db"
    from hanoi_heart_assistant.tools import appointment_tools
    from hanoi_heart_assistant import schedule_api
    
    monkeypatch.setattr(appointment_tools, "DB_PATH", temp_db)
    monkeypatch.setattr(schedule_api, "DB", temp_db)
    schedule_api.init_db()
    
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    import sqlite3
    with sqlite3.connect(temp_db) as con:
        import_id = con.execute(
            "INSERT INTO schedule_imports(original_name, file_path, sheet_name, title, week_start, week_end, status, created_at) VALUES(?,?,?,?,?,?,?,?)",
            ("test.xlsx", "test.xlsx", "Lich", "LICH TEST", tomorrow, tomorrow, "published", "2026-07-17T12:00:00")
        ).lastrowid
        area_id = con.execute("INSERT INTO schedule_areas(import_id, name, sort_order) VALUES(?,?,?)", (import_id, "Khu", 1)).lastrowid
        room_id = con.execute("INSERT INTO schedule_rooms(area_id, name, work_time, sort_order) VALUES(?,?,?,?)", (area_id, "P306", "7:00-16:30", 1)).lastrowid
        day_id = con.execute("INSERT INTO schedule_days(import_id, work_date, label, sort_order) VALUES(?,?,?,?)", (import_id, tomorrow, "Thứ 2", 1)).lastrowid
        con.execute(
            "INSERT INTO schedule_shifts(room_id, day_id, shift, state, value, booked_count, updated_at) VALUES(?,?,?,?,?,?,?)",
            (room_id, day_id, "morning", "working", "TS.BS Phạm Như Hùng", 0, "2026-07-17T12:00:00")
        )
        
    class MockFirestore:
        def collection(self, name):
            return self
        def document(self, name):
            return self
        def set(self, data):
            pass
            
    from hanoi_heart_assistant.tools import firebase_vector_tools
    monkeypatch.setattr(firebase_vector_tools, "_firestore_client", lambda: MockFirestore())
    
    result = submit_appointment_request(
        "Nguyễn Văn An", "0912345678", "tim_mach", tomorrow, "08:00", "Khám định kỳ", "TS.BS Phạm Như Hùng"
    )
    assert result["status"] == "success"
    assert result["code"].startswith("BVT-")

