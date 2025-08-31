from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import exists
from api.auth import create_token, require_auth, verify_password
from api.utils.detector_gemini import judge_claim_with_gemini

from sqlalchemy.orm import Session
import uuid

from api.model.db import FactCheckerUser, FactCheckerVote, SessionLocal, init_db, Claim
from api.utils.init_claims import seed_claims
from api.utils.init_fact_checkers import seed_fact_checkers

app = Flask(__name__)
CORS(
    app,
    resources={r"/*": {"origins": ["http://localhost:5173"]}},
    supports_credentials=True,
    expose_headers=["Authorization", "Content-Type"],
)
init_db()
seed_fact_checkers()
seed_claims()

@app.post("/auth/signin")
def signin():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify(error="email and password required"), 400

    db: Session = SessionLocal()
    try:
        user = db.query(FactCheckerUser).filter(FactCheckerUser.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            return jsonify(error="invalid credentials"), 401

        token = create_token(user)
        return jsonify(
            access_token=token,
            user={"id": user.id, "email": user.email, "name": user.name, "org": user.organization, "role": user.role}
        )
    finally:
        db.close()

@app.post("/check-claim")
def check_claim():
    data = request.get_json(force=True)
    claim = data.get("claim", "").strip()
    if not claim:
        return jsonify(error="claim is required"), 400

    result = judge_claim_with_gemini(claim)

    return jsonify(result)


@app.post("/claims")
def create_claim():
    data = request.get_json(force=True)
    claim_text = data.get("claim", "").strip()
    if not claim_text:
        return jsonify(error="claim is required"), 400

    # Step 1: Create DB record
    claim_id = str(uuid.uuid4())
    db: Session = SessionLocal()
    new_claim = Claim(id=claim_id, claim_text=claim_text, status="pending")
    db.add(new_claim)
    db.commit()

    # Step 2: Run Gemini fact checker
    result = judge_claim_with_gemini(claim_text)

    # Step 3: Update DB record with status
    decision = result["result"]
    explanation = result.get("explanation", "")

    if decision == "NOT ENOUGH EVIDENCE":
        status = "escalated_manual"
    elif decision == "TRUE":
        status = "true"
    elif decision == "FALSE":
        status = "false"
    else:
        status = "unknown"

    new_claim.status = status
    new_claim.explanation = explanation
    db.add(new_claim)
    db.commit()

    return jsonify({
        "id": claim_id,
        "claim": claim_text,
    })

@app.get("/fact-checkers/<user_id>/escalated")
@require_auth
def list_escalated_for_user(user_id):
    """
    Return escalated_manual claims that THIS user hasn't voted on yet.
    Supports basic pagination: ?limit=20&offset=0
    """
    limit = int(request.args.get("limit", 20))
    offset = int(request.args.get("offset", 0))
 
    db: Session = SessionLocal()
    try:
        # subquery: votes by this user
        subq = db.query(FactCheckerVote.claim_id).filter(FactCheckerVote.user_id == user_id).subquery()

        # claims with status escalated_manual AND not in user's voted set
        q = (
            db.query(Claim)
              .filter(Claim.status == "escalated_manual")
              .filter(~Claim.id.in_(subq))
              .order_by(Claim.id)
              .offset(offset)
              .limit(limit)
        )

        items = q.all()
        results = [{
            "id": c.id,
            "claim": c.claim_text,
            "status": c.status,
            "explanation": c.explanation,
            "truth_count": c.truth_count,
            "false_count": c.false_count,
        } for c in items]

        return jsonify({
            "user_id": user_id,
            "count": len(results),
            "items": results,
            "limit": limit,
            "offset": offset
        })
    finally:
        db.close()

@app.post("/claims/<claim_id>/vote")
@require_auth
def vote_claim(claim_id):
    """
    Body: { "user_id": "...", "vote": "true" | "false" }
    Records a vote (idempotent per user/claim), bumps counters on the claim.
    """
    data = request.get_json(force=True)
    user_id = (data.get("user_id") or "").strip()
    vote = (data.get("vote") or "").strip().lower()

    if not user_id:
        return jsonify(error="user_id is required"), 400
    if vote not in ("true", "false"):
        return jsonify(error="vote must be 'true' or 'false'"), 400

    db: Session = SessionLocal()
    try:
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            return jsonify(error="Claim not found"), 404
        if claim.status != "escalated_manual":
            return jsonify(error="Voting allowed only on escalated_manual claims"), 400

        # Check if this user already voted on this claim
        already = db.query(
            exists().where(
                (FactCheckerVote.claim_id == claim_id) &
                (FactCheckerVote.user_id == user_id)
            )
        ).scalar()

        if already:
            return jsonify(error="User already voted on this claim"), 409

        # Record vote
        v = FactCheckerVote(
            id=str(uuid.uuid4()),
            claim_id=claim_id,
            user_id=user_id,
            vote=vote
        )
        db.add(v)

        # Increment counters
        if vote == "true":
            claim.truth_count += 1
        else:
            claim.false_count += 1

        db.add(claim)
        db.commit()

        return jsonify({
            "claim_id": claim.id,
            "user_id": user_id,
            "vote": vote,
            "truth_count": claim.truth_count,
            "false_count": claim.false_count
        })
    finally:
        db.close()

@app.get("/claims/escalated")
def get_escalated_claims():
    db: Session = SessionLocal()
    try:
        escalated = db.query(Claim).filter(Claim.status == "escalated_manual").all()
        results = []
        for c in escalated:
            results.append({
                "id": c.id,
                "claim": c.claim_text,
                "status": c.status,
                "explanation": c.explanation,
                "truth_count": c.truth_count,
                "false_count": c.false_count,
            })
        return jsonify(results)
    finally:
        db.close()



@app.get("/claims/<claim_id>")
def get_claim_status(claim_id):
    """
    Retrieve claim details by claim_id
    """
    db: Session = SessionLocal()
    try:
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            return jsonify(error="Claim not found"), 404

        return jsonify({
            "id": claim.id,
            "claim": claim.claim_text,
            "status": claim.status,
            "explanation": claim.explanation,
            "truth_count": claim.truth_count,
            "false_count": claim.false_count
        })
    finally:
        db.close()

@app.get("/claims")
def list_claims():

    status = request.args.get("status")

    db: Session = SessionLocal()
    try:
        query = db.query(Claim)
        if status:
            query = query.filter(Claim.status == status)

        claims = query.all()
        results = []
        for c in claims:
            results.append({
                "id": c.id,
                "claim": c.claim_text,
                "status": c.status,
                "explanation": c.explanation,
                "truth_count": c.truth_count,
                "false_count": c.false_count,
            })

        return jsonify(results)
    finally:
        db.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
