import datetime
import uuid
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Text, Integer, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
DATABASE_URL = "sqlite:///claims.db"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class FactCheckerUser(Base):
    __tablename__ = "fact_checker_users"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    organization = Column(String, nullable=False)
    role = Column(String, default="fact_checker")
    password_hash = Column(String, nullable=False)      # <— NEW
    votes = relationship("FactCheckerVote", back_populates="user")

class FactCheckerVote(Base):
    __tablename__ = "fact_checker_votes"
    id = Column(String, primary_key=True)
    claim_id = Column(String, ForeignKey("claims.id"), index=True, nullable=False)
    user_id = Column(String, ForeignKey("fact_checker_users.id"), index=True, nullable=False)
    vote = Column(String, nullable=False)               # "true" | "false"
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("claim_id", "user_id", name="uq_vote_claim_user"),)
    claim = relationship("Claim", back_populates="votes")
    user  = relationship("FactCheckerUser", back_populates="votes")


class Claim(Base):
    __tablename__ = "claims"
    id = Column(String, primary_key=True, index=True)
    claim_text = Column(Text, nullable=False)
    status = Column(String, default="pending")          # pending | true | false | escalated_manual
    explanation = Column(Text, nullable=True)
    truth_count = Column(Integer, default=0)
    false_count = Column(Integer, default=0)
    votes = relationship("FactCheckerVote", back_populates="claim")

def init_db():
    Base.metadata.create_all(bind=engine)