import os, datetime, functools
import jwt
from flask import request, jsonify, g
from passlib.hash import bcrypt
from sqlalchemy.orm import Session

from api.model.db import SessionLocal, FactCheckerUser

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALG    = "HS256"
JWT_TTL_MIN= int(os.getenv("JWT_TTL_MIN", "120"))

def create_token(user: FactCheckerUser) -> str:
    now = datetime.datetime.utcnow()
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "iat": now,
        "exp": now + datetime.timedelta(minutes=JWT_TTL_MIN),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def verify_password(pw: str, password_hash: str) -> bool:
    return bcrypt.verify(pw, password_hash)

def require_auth(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify(error="Missing/invalid Authorization header"), 401
        token = auth.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        except jwt.PyJWTError:
            return jsonify(error="Invalid or expired token"), 401

        # attach current user to request context
        db: Session = SessionLocal()
        try:
            user = db.query(FactCheckerUser).filter(FactCheckerUser.id == payload["sub"]).first()
            if not user:
                return jsonify(error="User not found"), 401
            g.current_user = user
            return func(*args, **kwargs)
        finally:
            db.close()
    return wrapper