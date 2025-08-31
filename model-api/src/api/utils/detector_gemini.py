# file: model/gemini_judge.py
from __future__ import annotations
import os, json
from typing import Dict, Any, Optional

import google.generativeai as genai
from api.utils.retrieve import Retriever   # <-- your retriever class

_SYSTEM = (
    "You are a strict fact checker. Decide TRUE, FALSE, or NOT ENOUGH EVIDENCE "
    "for the claim using ONLY the evidence provided. If numbers/years/units "
    "don’t exactly match, answer NOT ENOUGH EVIDENCE.\n\n"
    'Return ONLY this JSON: {"result":"TRUE|FALSE|NOT ENOUGH EVIDENCE","explanation":"one short sentence"}'
)

def _ensure_gemini(model_name: str, api_key: Optional[str]) -> genai.GenerativeModel:
    key = api_key or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_API_KEY not set")
    genai.configure(api_key=key)
    return genai.GenerativeModel(model_name)

def judge_claim_with_gemini(
    claim: str,
    *,
    model_name: str = "gemini-1.5-flash",
    temperature: float = 0.0,
    api_key: Optional[str] = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Given a claim, retrieves evidence from Qdrant and asks Gemini to fact-check it.
    Returns: {"result": "TRUE|FALSE|NOT ENOUGH EVIDENCE", "explanation": "...", "evidence": [...], "raw": "..."}
    """

    # Step 1: Retrieve evidence from Qdrant
    retriever = Retriever()
    hits = retriever.search(claim, top_k=top_k)
    evidences = [h.payload["fact_text"] for h in hits]

    # Step 2: Prepare prompt
    ev_block = "\n".join(f"- {e}" for e in evidences) if evidences else "- (no evidence found)"
    prompt = f"{_SYSTEM}\n\nClaim:\n{claim}\n\nEvidence:\n{ev_block}\n"

    # Step 3: Call Gemini
    model = _ensure_gemini(model_name, api_key)
    generation_config = {
        "temperature": temperature,
        "response_mime_type": "application/json",
    }

    resp = model.generate_content(prompt, generation_config=generation_config)
    raw = getattr(resp, "text", "") or ""

    # Step 4: Robust JSON parse
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        parsed = json.loads(raw[start:end+1]) if (start >= 0 and end > start) else {
            "result": "NOT ENOUGH EVIDENCE",
            "explanation": "Could not parse model response."
        }

    parsed.setdefault("result", "NOT ENOUGH EVIDENCE")
    parsed.setdefault("explanation", "No explanation provided.")
    parsed["evidence"] = evidences
    parsed["raw"] = raw
    return parsed
