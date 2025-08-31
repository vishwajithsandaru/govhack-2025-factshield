import uuid
from passlib.hash import bcrypt
from api.model.db import SessionLocal, init_db, FactCheckerUser

def seed_fact_checkers():
    init_db()
    db = SessionLocal()

    # Hardcoded demo passwords — CHANGE THESE in real use
    users = [
        dict(
            id=str(uuid.uuid4()),
            name="Alice Johnson",
            email="alice@example.org",
            organization="TruthCheck Org",
            role="senior_fact_checker",
            password_hash=bcrypt.hash("alice-pass"),
        ),
        dict(
            id=str(uuid.uuid4()),
            name="Bob Smith",
            email="bob@example.org",
            organization="NewsTrust",
            role="fact_checker",
            password_hash=bcrypt.hash("bob-pass"),
        ),
        dict(
            id=str(uuid.uuid4()),
            name="Clara Martinez",
            email="clara@example.org",
            organization="FactFinders Inc.",
            role="fact_checker",
            password_hash=bcrypt.hash("clara-pass"),
        ),
    ]

    for u in users:
        if not db.query(FactCheckerUser).filter_by(email=u["email"]).first():
            db.add(FactCheckerUser(**u))

    db.commit()
    db.close()
    print("✅ Seeded fact-checkers with bcrypt passwords")
