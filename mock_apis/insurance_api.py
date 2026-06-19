"""
Mock Insurance APIs for Insurer1 (Plan A) and Insurer2 (Plan B).
Run with: uvicorn mock_apis.insurance_api:app --port 8000
"""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Mock Insurance APIs — DuCO-Agent")

PREAUTH_REQUIRED_CPTS = {"29888", "29881", "73721", "27447"}

PLAN_A = {
    "insurer": "Insurer1",
    "plan": "Plan A",
    "annual_deductible_inr": 10000,
    "coinsurance_plan_pct": 80,
    "oop_max_inr": 75000,
    "network_hospitals": ["Sterling Orthopedic Hospital", "Apollo Mumbai"],
    "cob_role_for_dependent_aarav": "secondary",
    "cob_role_for_primary_priya": "primary",
}

PLAN_B = {
    "insurer": "Insurer2",
    "plan": "Plan B",
    "annual_deductible_inr": 15000,
    "coinsurance_plan_pct": 80,
    "oop_max_inr": 100000,
    "network_hospitals": ["Sterling Orthopedic Hospital", "Lilavati Hospital"],
    "cob_role_for_primary_aarav": "primary",
    "cob_role_for_dependent_priya": "secondary",
}


@app.get("/api/insurer1/plan")
def get_plan_a():
    return PLAN_A


@app.get("/api/insurer2/plan")
def get_plan_b():
    return PLAN_B


class PreAuthRequest(BaseModel):
    cpt_code: str
    patient: str
    insurer: str


@app.post("/api/verify-preauth")
def verify_preauth(req: PreAuthRequest):
    required = req.cpt_code in PREAUTH_REQUIRED_CPTS
    return {
        "cpt_code": req.cpt_code,
        "preauth_required": required,
        "status": "APPROVED" if required else "NOT_REQUIRED",
        "validity_days": 90 if required else None,
        "notes": (
            "ACL reconstruction requires pre-auth. Letter must be submitted 48hr before surgery."
            if required
            else None
        ),
    }


@app.get("/api/cob-rules")
def get_cob_rules():
    return {
        "rule": "Employment-based Birthday Rule",
        "description": (
            "Each insured's own employer plan is primary for their own claims. "
            "Spouse's plan is secondary."
        ),
        "aarav": {"primary": "Plan B (Insurer2)", "secondary": "Plan A (Insurer1)"},
        "priya": {"primary": "Plan A (Insurer1)", "secondary": "Plan B (Insurer2)"},
    }
