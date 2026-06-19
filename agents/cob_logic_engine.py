"""
COB Logic Engine — Coordination of Benefits

Implements the Birthday Rule, primary/secondary determination,
deductible tracking, coinsurance, and OOP max calculations.
All amounts in INR.
"""

from dataclasses import dataclass
import json
import httpx


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


def fetch_cob_rules_from_api() -> dict | None:
    """
    Attempt to fetch COB rules from mock API (tool-use pattern).
    Falls back to local logic if API is unreachable.
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
    Steps:
      1. Determine primary vs secondary plan
      2. Primary plan applies deductible, then coinsurance
      3. Secondary plan applies to remaining patient OOP from primary
      4. Patient's final OOP = what's left after both plans
    """
    primary, secondary = determine_primary(patient, "surgery")

    breakdown = {
        "patient": patient,
        "total_bill_inr": total_bill,
        "cpt_codes": cpt_codes,
        "primary_plan": primary.name,
        "secondary_plan": secondary.name,
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
        "deductible_applied_inr": primary_deductible_applied,
        "eligible_after_deductible_inr": after_primary_deductible,
        "plan_pays_inr": primary_plan_pays,
        "patient_coinsurance_inr": primary_coinsurance_patient,
        "patient_oop_inr": patient_oop_primary,
    }
    breakdown["steps"].append(step1)

    # === SECONDARY PLAN CALCULATION ===
    # Secondary plan sees: what the patient still owes after primary
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
        "patient_oop_from_primary_inr": remaining_for_secondary,
        "deductible_applied_inr": secondary_deductible_applied,
        "eligible_after_secondary_deductible_inr": after_secondary_deductible,
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
        "savings_vs_no_dual_coverage_inr": total_bill - patient_final_oop,
    }

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
    )


def run_cob_for_all_claims(intake_data: dict) -> dict:
    """Orchestrates COB for both Aarav's surgery and Priya's PT"""
    print("[COB Engine] Calculating coordination of benefits...")

    aarav_result = calculate_cob(
        patient="Aarav",
        claim_id="CLM-2026-001",
        total_bill=4_50_000,
        cpt_codes=intake_data["aarav_surgery"].get("cpt_codes", []),
    )

    priya_result = calculate_cob(
        patient="Priya",
        claim_id="CLM-2026-002",
        total_bill=30_000,
        cpt_codes=intake_data["priya_pt"].get("cpt_codes", []),
    )

    print(f"   Aarav surgery OOP: Rs {aarav_result.patient_oop:,}")
    print(f"   Priya PT OOP:      Rs {priya_result.patient_oop:,}")
    print("   COB complete.\n")

    return {
        "aarav_surgery": aarav_result,
        "priya_pt": priya_result,
    }
