# file: init_claims.py
import uuid
from model.db import SessionLocal, init_db, Claim

def seed_claims():
    init_db()
    db = SessionLocal()

    claims = [
        # Likely TRUE
        {
            "claim_text": "In 2012, New Zealand exported 1,123,294 tonnes of whole milk powder.",
            "status": "true",
            "explanation": "Matches export dataset",
            "truth_count": 3,
            "false_count": 0,
        },
        {
            "claim_text": "In 2014, export revenue from cheese was 5,575 million $NZ.",
            "status": "true",
            "explanation": "Dataset confirms value",
            "truth_count": 2,
            "false_count": 0,
        },
        {
            "claim_text": "Average export price for butter in 2013 was 3,500 $NZ/tonne.",
            "status": "true",
            "explanation": "Consistent with records",
            "truth_count": 1,
            "false_count": 0,
        },
        {
            "claim_text": "New Zealand exported over 1 million tonnes of whole milk powder in 2013.",
            "status": "true",
            "explanation": "Slightly above 1 million according to stats",
            "truth_count": 1,
            "false_count": 0,
        },
        {
            "claim_text": "Casein export revenue in 2012 exceeded 1,000 million $NZ.",
            "status": "true",
            "explanation": "Dataset shows above threshold",
            "truth_count": 2,
            "false_count": 0,
        },

        # Likely FALSE
        {
            "claim_text": "In 2015, cheese exports from New Zealand exceeded 5 million tonnes.",
            "status": "false",
            "explanation": "Dataset shows far lower volume",
            "truth_count": 0,
            "false_count": 4,
        },
        {
            "claim_text": "New Zealand exported 10 million tonnes of butter in 2014.",
            "status": "false",
            "explanation": "Exports never reached this level",
            "truth_count": 0,
            "false_count": 2,
        },
        {
            "claim_text": "Skim milk powder exports in 2013 were less than 100 tonnes.",
            "status": "false",
            "explanation": "Dataset shows much higher figures",
            "truth_count": 0,
            "false_count": 3,
        },
        {
            "claim_text": "Export revenue from casein in 2014 was 50 million $NZ.",
            "status": "false",
            "explanation": "Dataset shows revenue in the hundreds of millions",
            "truth_count": 0,
            "false_count": 3,
        },
        {
            "claim_text": "In 2012, butter exports accounted for 90% of all dairy exports.",
            "status": "false",
            "explanation": "Whole milk powder dominated exports, not butter",
            "truth_count": 0,
            "false_count": 2,
        },

        # Escalated Manual
        {
            "claim_text": "New Zealand exported 750,000 tonnes of skim milk powder in 2014.",
            "status": "escalated_manual",
            "explanation": "Conflicting numbers in dataset",
            "truth_count": 0,
            "false_count": 0,
        },
        {
            "claim_text": "Average export price of cheese in 2013 was exactly 4,000 $NZ/tonne.",
            "status": "escalated_manual",
            "explanation": "Close to dataset values but needs verification",
            "truth_count": 0,
            "false_count": 0,
        },
        {
            "claim_text": "Export revenue from whole milk powder in 2015 was 8,000 million $NZ.",
            "status": "escalated_manual",
            "explanation": "Value may be slightly lower or higher, requires review",
            "truth_count": 0,
            "false_count": 0,
        },
        {
            "claim_text": "In 2014, butter exports reached exactly 500,000 tonnes.",
            "status": "escalated_manual",
            "explanation": "Dataset shows similar but not exact number",
            "truth_count": 0,
            "false_count": 0,
        },
        {
            "claim_text": "Casein exports in 2013 were the largest among dairy categories.",
            "status": "escalated_manual",
            "explanation": "Dataset suggests whole milk powder was larger",
            "truth_count": 0,
            "false_count": 0,
        },
    ]

    for c in claims:
        if not db.query(Claim).filter_by(claim_text=c["claim_text"]).first():
            new_claim = Claim(
                id=str(uuid.uuid4()),
                claim_text=c["claim_text"],
                status=c["status"],
                explanation=c["explanation"],
                truth_count=c["truth_count"],
                false_count=c["false_count"],
            )
            db.add(new_claim)

    db.commit()
    db.close()
    print(f"✅ Seeded {len(claims)} sample claims")