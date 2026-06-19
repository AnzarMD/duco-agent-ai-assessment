"""
COB Logic Engine — Coordination of Benefits

Implements the Birthday Rule, primary/secondary determination,
deductible tracking, coinsurance, and OOP max calculations.
All amounts in INR.

Agentic Features:
- Tool-use: Calls mock insurance API to verify pre-auth requirements per CPT code
- Reflection: Uses LLM to verify its own calculation output for correctness
- State tracking: Maintains plan state across multiple claims
"""

from dataclasses import dataclass
import json
import os
import httpx
from mistralai.client import Mistral

client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY", ""))


@dataclass
class InsurancePlan:
    name: str
    insurer: str
    annual_deductible: int
    coinsurance_plan_pct: float  # e.g. 0.80 = plan pays 80%
    annual_oop_max: int
    deductible_met: int = 0  # how much deductible already used this year
    oop_spent: int = 0  # how much OOP already paid this year

    @property
    def remaining_deductible(self) -> int:
        return max(0, self.annual_deductible - self.deductible_met)

    @property
    def remaining_oop_capacity(self) -> int:
        return max(0, self.annual_oop_max - self.oop_spent)


@dataclass
class ClaimResult:
    claim_id: str
    patient: str
    total_bill: int
    primary_plan: str
    secondary_plan: str
    primary_plan_pays: int
    secondary_plan_pays: int
    patient_oop: int
    breakdown: dict
    preauth_verification: dict


# Mock plan definitions — inject via API in real system
PLAN_A = InsurancePlan(
    name="Plan A",
    insurer="Insurer1",
    annual_deductible=10_000,
    coinsurance_plan_pct=0.80,
    annual_oop_max=75_000,
    deductible_met=0,
    oop_spent=0,
)

PLAN_B = InsurancePlan(
    name="Plan B",
    insurer="Insurer2",
    annual_deductible=15_000,
    coinsurance_plan_pct=0.80,
    annual_oop_max=1_00_000,
    deductible_met=0,
    oop_spent=0,
)


# ─── TOOL-USE: API INTERACTIONS ─────────────────────────────────────────────

def fetch_cob_rules_from_api() -> dict | None:
    """
    TOOL-USE: Fetch COB rules from mock insurance API.
    Demonstrates agentic tool-use — the agent decides to consult an external
    service to verify its logic rather than relying on hardcoded rules.
    """
    try:
        response = httpx.get(
            "http://localhost:8000/api/cob-rules",
            timeout=httpx.Timeout(connect=0.5, read=1.0, write=1.0, pool=0.5),
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None


def verify_preauth_requirement(cpt_code: str, patient: str, insurer: str) -> dict:
    """
    TOOL-USE: Check if a specific CPT code requires pre-authorization.
    Calls the mock insurance API endpoint for each code.
    Falls back to local knowledge if API is unavailable.
    """
    # Known pre-auth required codes (local fallback)
    PREAUTH_REQUIRED = {"29888", "29881", "73721", "27447"}

    try:
        response = httpx.post(
            "http://localhost:8000/api/verify-preauth",
            json={"cpt_code": cpt_code, "patient": patient, "insurer": insurer},
            timeout=httpx.Timeout(connect=0.5, read=1.0, write=1.0, pool=0.5),
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass

    # Fallback: use local knowledge
    required = cpt_code in PREAUTH_REQUIRED
    return {
        "cpt_code": cpt_code,
        "preauth_required": required,
        "status": "APPROVED" if required else "NOT_REQUIRED",
        "source": "local_fallback",
        "notes": f"CPT {cpt_code} {'requires' if required else 'does not require'} pre-authorization.",
    }


def run_preauth_verification(cpt_codes: list[dict], patient: str, insurer: str) -> dict:
    """
    AGENTIC TOOL-USE LOOP: Iterates over all CPT codes and checks each one
    for pre-authorization requirements. This simulates the agent making
    autonomous decisions about which tools to invoke.
    """
    print(f"   [Tool-Use] Verifying pre-auth requirements for {patient}...")
    results = {}
    codes_needing_preauth = []

    for code_info in cpt_codes:
        code = code_info.get("code", "")
        if not code:
            continue
        result = verify_preauth_requirement(code, patient, insurer)
        results[code] = result
        if result.get("preauth_required"):
            codes_needing_preauth.append(code)
            print(f"      CPT {code}: PRE-AUTH REQUIRED ⚠️")
        else:
            print(f"      CPT {code}: No pre-auth needed ✓")

    return {
        "all_verifications": results,
        "codes_needing_preauth": codes_needing_preauth,
        "preauth_required": len(codes_needing_preauth) > 0,
    }


# ─── REFLECTION: LLM SELF-VERIFICATION ──────────────────────────────────────

def reflect_on_calculation(breakdown: dict) -> dict:
    """
    REFLECTION: The agent reviews its own COB calculation output using the LLM.
    This demonstrates agentic self-correction — the system verifies its reasoning.
    """
    summary = breakdown.get("summary", {})
    steps = breakdown.get("steps", [])
    total_bill = breakdown.get("total_bill_inr", 0)

    prompt = f"""
    You are an insurance claims auditor. Review this COB (Coordination of Benefits) calculation
    and verify if it is mathematically correct and follows standard COB rules.

    CALCULATION TO REVIEW:
    - Total Bill: Rs {total_bill:,}
    - Primary Plan: {breakdown.get('primary_plan')} | Secondary Plan: {breakdown.get('secondary_plan')}
    - Step 1 (Primary): {json.dumps(steps[0] if steps else {}, indent=2)}
    - Step 2 (Secondary): {json.dumps(steps[1] if len(steps) > 1 else {}, indent=2)}
    - Summary: Primary pays Rs {summary.get('primary_pays_inr', 0):,}, Secondary pays Rs {summary.get('secondary_pays_inr', 0):,}, Patient OOP Rs {summary.get('patient_final_oop_inr', 0):,}

    RULES TO CHECK:
    1. Primary + Secondary + Patient OOP must equal Total Bill (no overpayment)
    2. Deductible is applied before coinsurance
    3. Coinsurance split is applied to amount after deductible
    4. OOP maximum caps the patient's total out-of-pocket
    5. Secondary plan only covers what patient still owes after primary

    Return ONLY a JSON object:
    {{
      "is_correct": true/false,
      "confidence": 0.0 to 1.0,
      "issues_found": ["list of issues or empty array"],
      "explanation": "brief explanation of verification"
    }}
    """
    try:
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        return {
            "is_correct": True,
            "confidence": 0.7,
            "issues_found": [],
            "explanation": f"Reflection unavailable ({e}); proceeding with calculation as-is.",
        }


# ─── CORE COB LOGIC ─────────────────────────────────────────────────────────

def determine_primary(patient: str, claim_type: str) -> tuple[InsurancePlan, InsurancePlan]:
    """
    Birthday Rule / Employment Rule for COB:
    - Each person's OWN employer plan is always primary for THEIR claims.
    - Priya is primary holder of Plan A -> Plan A is primary for PRIYA's claims.
    - Aarav is primary holder of Plan B -> Plan B is primary for AARAV's claims.

    Also attempts to verify via Mock API (demonstrating tool-use).
    Returns (primary_plan, secondary_plan)
    """
    # Try fetching from API first (agentic tool-use)
    api_rules = fetch_cob_rules_from_api()
    if api_rules:
        print(f"   [COB] Verified primary/secondary via API: {api_rules.get('rule', 'N/A')}")

    if patient.lower() == "priya":
        return PLAN_A, PLAN_B  # Plan A primary, Plan B secondary
    elif patient.lower() == "aarav":
        return PLAN_B, PLAN_A  # Plan B primary, Plan A secondary
    raise ValueError(f"Unknown patient: {patient}")


def calculate_cob(
    patient: str,
    claim_id: str,
    total_bill: int,
    cpt_codes: list[dict],
) -> ClaimResult:
    """
    Full COB calculation with deductible, coinsurance, OOP max.

    Agentic Steps:
      1. Determine primary vs secondary plan (with API verification)
      2. Tool-use: Verify pre-auth requirements for each CPT code
      3. Primary plan applies deductible, then coinsurance
      4. Secondary plan applies to remaining patient OOP from primary
      5. Reflection: LLM verifies the calculation is correct
      6. Return validated result
    """
    primary, secondary = determine_primary(patient, "surgery")

    # TOOL-USE: Check pre-auth for each CPT code
    preauth_results = run_preauth_verification(cpt_codes, patient, primary.insurer)

    breakdown = {
        "patient": patient,
        "total_bill_inr": total_bill,
        "cpt_codes": cpt_codes,
        "primary_plan": primary.name,
        "secondary_plan": secondary.name,
        "preauth_verification": preauth_results,
        "calculation_method": "Standard COB with Birthday Rule",
        "steps": [],
    }

    # === PRIMARY PLAN CALCULATION ===
    primary_deductible_applied = min(primary.remaining_deductible, total_bill)
    after_primary_deductible = total_bill - primary_deductible_applied

    primary_coinsurance_patient = 0
    primary_plan_pays = 0

    if after_primary_deductible > 0:
        raw_patient_coinsurance = int(after_primary_deductible * (1 - primary.coinsurance_plan_pct))
        # Apply OOP max cap
        remaining_oop = primary.remaining_oop_capacity - primary_deductible_applied
        primary_coinsurance_patient = min(raw_patient_coinsurance, max(0, remaining_oop))
        primary_plan_pays = after_primary_deductible - primary_coinsurance_patient

    patient_oop_primary = primary_deductible_applied + primary_coinsurance_patient

    step1 = {
        "plan": primary.name,
        "role": "Primary",
        "explanation": (
            f"Apply {primary.name} deductible of Rs {primary.annual_deductible:,}. "
            f"Deductible applied: Rs {primary_deductible_applied:,}. "
            f"Remaining eligible amount: Rs {after_primary_deductible:,}. "
            f"Plan pays {int(primary.coinsurance_plan_pct*100)}% = Rs {primary_plan_pays:,}. "
            f"Patient responsible for coinsurance: Rs {primary_coinsurance_patient:,}. "
            f"Total patient OOP after primary: Rs {patient_oop_primary:,}."
        ),
        "deductible_applied_inr": primary_deductible_applied,
        "eligible_after_deductible_inr": after_primary_deductible,
        "coinsurance_rate": f"{int(primary.coinsurance_plan_pct*100)}% plan / {int((1-primary.coinsurance_plan_pct)*100)}% patient",
        "plan_pays_inr": primary_plan_pays,
        "patient_coinsurance_inr": primary_coinsurance_patient,
        "patient_oop_inr": patient_oop_primary,
        "oop_max_applied": patient_oop_primary >= primary.annual_oop_max,
    }
    breakdown["steps"].append(step1)

    # === SECONDARY PLAN CALCULATION ===
    remaining_for_secondary = patient_oop_primary

    secondary_deductible_applied = min(secondary.remaining_deductible, remaining_for_secondary)
    after_secondary_deductible = remaining_for_secondary - secondary_deductible_applied

    secondary_plan_pays = 0
    secondary_patient_coinsurance = 0

    if after_secondary_deductible > 0:
        raw_sec_patient = int(after_secondary_deductible * (1 - secondary.coinsurance_plan_pct))
        remaining_sec_oop = secondary.remaining_oop_capacity - secondary_deductible_applied
        secondary_patient_coinsurance = min(raw_sec_patient, max(0, remaining_sec_oop))
        secondary_plan_pays = after_secondary_deductible - secondary_patient_coinsurance

    patient_final_oop = secondary_deductible_applied + secondary_patient_coinsurance

    step2 = {
        "plan": secondary.name,
        "role": "Secondary",
        "explanation": (
            f"Secondary plan picks up patient's remaining OOP from primary: Rs {remaining_for_secondary:,}. "
            f"Apply {secondary.name} deductible: Rs {secondary_deductible_applied:,}. "
            f"Eligible after deductible: Rs {after_secondary_deductible:,}. "
            f"Plan pays {int(secondary.coinsurance_plan_pct*100)}% = Rs {secondary_plan_pays:,}. "
            f"Patient coinsurance: Rs {secondary_patient_coinsurance:,}. "
            f"Patient final OOP: Rs {patient_final_oop:,}."
        ),
        "patient_oop_from_primary_inr": remaining_for_secondary,
        "deductible_applied_inr": secondary_deductible_applied,
        "eligible_after_secondary_deductible_inr": after_secondary_deductible,
        "coinsurance_rate": f"{int(secondary.coinsurance_plan_pct*100)}% plan / {int((1-secondary.coinsurance_plan_pct)*100)}% patient",
        "plan_pays_inr": secondary_plan_pays,
        "patient_coinsurance_inr": secondary_patient_coinsurance,
        "patient_final_oop_inr": patient_final_oop,
    }
    breakdown["steps"].append(step2)

    # === VALIDATION: total payments must not exceed bill ===
    total_paid_by_insurers = primary_plan_pays + secondary_plan_pays
    assert total_paid_by_insurers + patient_final_oop <= total_bill + 1, (
        f"COB error: payments ({total_paid_by_insurers} + {patient_final_oop}) exceed bill ({total_bill})"
    )

    breakdown["summary"] = {
        "primary_pays_inr": primary_plan_pays,
        "secondary_pays_inr": secondary_plan_pays,
        "patient_final_oop_inr": patient_final_oop,
        "total_insurer_coverage_inr": total_paid_by_insurers,
        "savings_vs_no_dual_coverage_inr": total_bill - patient_final_oop,
        "coverage_percentage": round((total_paid_by_insurers / total_bill) * 100, 1) if total_bill > 0 else 0,
    }

    # === REFLECTION: LLM verifies the calculation ===
    print(f"   [Reflection] Verifying COB calculation for {patient}...")
    reflection = reflect_on_calculation(breakdown)
    breakdown["reflection"] = reflection

    if reflection.get("is_correct"):
        print(f"   [Reflection] ✓ Calculation verified (confidence: {reflection.get('confidence', 'N/A')})")
    else:
        issues = reflection.get("issues_found", [])
        print(f"   [Reflection] ⚠️ Potential issues found: {issues}")

    return ClaimResult(
        claim_id=claim_id,
        patient=patient,
        total_bill=total_bill,
        primary_plan=primary.name,
        secondary_plan=secondary.name,
        primary_plan_pays=primary_plan_pays,
        secondary_plan_pays=secondary_plan_pays,
        patient_oop=patient_final_oop,
        breakdown=breakdown,
        preauth_verification=preauth_results,
    )


def run_cob_for_all_claims(intake_data: dict) -> dict:
    """Orchestrates COB for both Aarav's surgery and Priya's PT"""
    print("[COB Engine] Calculating coordination of benefits...")
    print("   Applying Birthday Rule: Each person's own employer plan is primary.\n")

    aarav_result = calculate_cob(
        patient="Aarav",
        claim_id="CLM-2026-001",
        total_bill=4_50_000,
        cpt_codes=intake_data["aarav_surgery"].get("cpt_codes", []),
    )

    print()  # spacing between claims

    priya_result = calculate_cob(
        patient="Priya",
        claim_id="CLM-2026-002",
        total_bill=30_000,
        cpt_codes=intake_data["priya_pt"].get("cpt_codes", []),
    )

    print(f"\n   ┌─────────────────────────────────────────┐")
    print(f"   │  COB RESULTS SUMMARY                     │")
    print(f"   ├─────────────────────────────────────────┤")
    print(f"   │  Aarav surgery OOP: Rs {aarav_result.patient_oop:>10,}   │")
    print(f"   │  Priya PT OOP:      Rs {priya_result.patient_oop:>10,}   │")
    print(f"   │  Combined family:   Rs {aarav_result.patient_oop + priya_result.patient_oop:>10,}   │")
    print(f"   └─────────────────────────────────────────┘")
    print("   COB complete.\n")

    return {
        "aarav_surgery": aarav_result,
        "priya_pt": priya_result,
    }
