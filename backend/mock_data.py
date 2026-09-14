import hashlib
from sqlalchemy.orm import Session
from backend.database import VerifiedRegistry, SessionLocal, init_db


def hash_identifier(raw_id: str) -> str:
    """Normalize identifier (trim and uppercase) and compute SHA-256 hash."""
    normalized = raw_id.strip().upper()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


SEED_STUDENTS = [
    {
        "student_name": "Sarah Jenkins",
        "student_id_raw": "STU-98421",
        "course": "B.Sc. Computer Science",
        "institution": "Apex National Institute of Technology",
        "marks_or_grade": "3.92 GPA",
        "issue_year": 2024,
    },
    {
        "student_name": "David Chen",
        "student_id_raw": "STU-77210",
        "course": "B.Tech Electrical Engineering",
        "institution": "Apex National Institute of Technology",
        "marks_or_grade": "91.5%",
        "issue_year": 2023,
    },
    {
        "student_name": "Priya Sharma",
        "student_id_raw": "STU-44109",
        "course": "B.Sc. Data Science",
        "institution": "Apex National Institute of Technology",
        "marks_or_grade": "3.85 GPA",
        "issue_year": 2024,
    },
    {
        "student_name": "Marcus Vance",
        "student_id_raw": "STU-11934",
        "course": "B.A. Economics & Finance",
        "institution": "Apex National Institute of Technology",
        "marks_or_grade": "Grade A+",
        "issue_year": 2022,
    },
    {
        "student_name": "Elena Rostova",
        "student_id_raw": "STU-65872",
        "course": "M.Sc. Cyber Security & Forensics",
        "institution": "Apex National Institute of Technology",
        "marks_or_grade": "3.78 GPA",
        "issue_year": 2025,
    },
]


def seed_mock_data(db: Session):
    """Seed 5 realistic mock student records into VerifiedRegistry if not present."""
    count = db.query(VerifiedRegistry).count()
    if count >= len(SEED_STUDENTS):
        return count

    added = 0
    for item in SEED_STUDENTS:
        id_hash = hash_identifier(item["student_id_raw"])
        existing = db.query(VerifiedRegistry).filter_by(student_id_hash=id_hash).first()
        if not existing:
            record = VerifiedRegistry(
                student_name=item["student_name"],
                student_id_raw=item["student_id_raw"],
                student_id_hash=id_hash,
                course=item["course"],
                institution=item["institution"],
                marks_or_grade=item["marks_or_grade"],
                issue_year=item["issue_year"],
            )
            db.add(record)
            added += 1

    db.commit()
    return db.query(VerifiedRegistry).count()


if __name__ == "__main__":
    init_db()
    with SessionLocal() as session:
        total = seed_mock_data(session)
        print(f"VerifiedRegistry initialized with {total} records.")
        for r in session.query(VerifiedRegistry).all():
            print(f" - {r.student_name} ({r.student_id_raw}): hash={r.student_id_hash[:16]}... | {r.marks_or_grade}")
