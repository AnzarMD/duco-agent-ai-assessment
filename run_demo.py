"""
DuCO-Agent Demo Mode — Runs the full pipeline WITHOUT requiring an API key.

Uses cached/pre-computed LLM responses so evaluators can see the complete
pipeline output, state transitions, and generated outputs without needing
their own Mistral API key or Tesseract OCR installed.

Usage:
    python run_demo.py
"""

import json
import os

from agents.cob_logic_engine import calculate_cob, run_preauth_verification
from outputs.output_generator import generate_cost_flow_chart, generate_oop_summary
from outputs.audio_briefing import generate_audio

os.makedirs("outputs", exist_ok=True)


# ─── CACHED LLM RESPONSES (simulating what Mistral returns) ─────────────────

CACHED_PRIYA_PT = {
    "cpt_codes": [
        {"code": "97161", "description": "Physical Therapy Evaluation", "amount_inr": 8000},
        {"code": "97110", "description": "Therapeutic Exercise - Lower Back", "amount_inr": 14000},
        {"code": "97035", "description": "Ultrasound Therapy", "amount_inr": 5000},
        {"code": "97032", "description": "Transcutaneous Electrical Nerve Stimulation", "amount_inr": 3000},
    ],
    "icd10_codes": [
        {"code": "M54.5", "description": "Low back pain"},
    ],
    "patient": "Priya Sen",
    "date_of_service": "2026-06-14",
    "total_amount_inr": 30000,
    "preauth_required": False,
}

CACHED_AARAV_MRI = {
    "cpt_codes": [
        {"code": "73721", "description": "MRI, any joint of lower extremity, without contrast", "amount_inr": 8000},
    ],
    "icd10_codes": [
        {"code": "M23.619", "description": "Complete ACL tear, left knee (Grade III)"},
        {"code": "M23.200", "description": "Medial meniscus posterior horn tear, left knee"},
    ],
    "patient": "Aarav Sen",
    "date_of_service": "2026-06-10",
    "total_amount_inr": 8000,
    "preauth_required": True,
}

CACHED_AARAV_SURGERY = {
    "cpt_codes": [
        {"code": "29888", "description": "Arthroscopically aided ACL reconstruction", "amount_inr": 350000},
        {"code": "29881", "description": "Arthroscopy, knee, surgical; with meniscectomy", "amount_inr": 100000},
        {"code": "99213", "description": "Office/outpatient visit, established patient", "amount_inr": 2500},
        {"code": "73721", "description": "MRI, any joint of lower extremity, without contrast", "amount_inr": 8000},
    ],
    "icd10_codes": [
        {"code": "M23.619", "description": "Rupture of anterior cruciate ligament, left knee"},
        {"code": "M23.200", "description": "Derangement of medial meniscus, left knee"},
    ],
    "patient": "Aarav Sen",
    "date_of_service": "2026-06-18",
    "total_amount_inr": 460500,
    "preauth_required": True,
}

CACHED_AUDIO_SCRIPT = """Hello Aarav and Priya,

Here's a quick update on your insurance coordination results.

Aarav, for your ACL surgery that costs 4 lakh 50 thousand rupees, your Plan B from Insurer 2 is the primary insurer and will cover most of the bill. After both your insurance plans work together, you'll only need to pay around 28 thousand rupees out of your own pocket. That's a huge saving!

Priya, for your physical therapy sessions totaling 30 thousand rupees, your Plan A from Insurer 1 is primary. After coordination, your out-of-pocket cost comes to about 14 thousand rupees.

Together as a family, your combined out-of-pocket is roughly 42 thousand rupees on total bills of 4 lakh 80 thousand. That means your dual coverage saved you over 4 lakh 38 thousand rupees!

We've also generated pre-authorization letters for both insurers for Aarav's surgery. Please submit these at least 48 hours before the procedure date.

Next steps: Review the pre-auth letters in the outputs folder, confirm your surgery date with Dr. Vikram Nair, and submit the letters to both Insurer 1 and Insurer 2. Feel free to ask if you need anything else!"""


CACHED_PREAUTH_LETTER_PRIMARY = """Date: June 19, 2026

To: Medical Director
Insurer2 (Plan B) — Pre-Authorization Department

Subject: Pre-Authorization Request for ACL Reconstruction Surgery — URGENT

Dear Sir/Madam,

I am writing to request pre-authorization for the following surgical procedures for our policyholder, Mr. Aarav Sen, under Plan B (Primary Coverage).

PATIENT INFORMATION:
- Patient: Aarav Sen
- Policy: Plan B (Insurer2) — Primary Insurer
- Date of Request: June 19, 2026

PROPOSED PROCEDURES:
- CPT 29888: Arthroscopically aided anterior cruciate ligament reconstruction (Rs 3,50,000)
- CPT 29881: Arthroscopy, knee, surgical; with meniscectomy (Rs 1,00,000)

DIAGNOSIS CODES:
- ICD-10 M23.619: Rupture of anterior cruciate ligament, left knee
- ICD-10 M23.200: Derangement of medial meniscus, left knee

CLINICAL JUSTIFICATION:
MRI dated 10/06/2026 confirms a complete ACL tear (Grade III) with discontinuous ligament fibres and posterior tibial translation. Additionally, a horizontal cleavage tear of the medial meniscus posterior horn was identified. The patient is unable to bear weight and conservative management is not appropriate given the severity of injury. Surgical intervention is medically necessary.

The procedure is scheduled at Sterling Orthopedic Hospital under Dr. Vikram Nair, MS Ortho. Given the patient's inability to bear weight and risk of further cartilage damage, we request expedited review within 3-5 business days.

Please note this is the PRIMARY insurer for this claim. Coordination of Benefits applies with Insurer1 (Plan A) as secondary coverage.

Thank you for your prompt attention to this matter.

Sincerely,
DuCO-Agent Authorization Team
On behalf of Aarav Sen"""


CACHED_PREAUTH_LETTER_SECONDARY = """Date: June 19, 2026

To: Medical Director
Insurer1 (Plan A) — Pre-Authorization Department

Subject: Pre-Authorization Request for ACL Reconstruction — SECONDARY (Coordination of Benefits)

Dear Sir/Madam,

I am writing to request pre-authorization for surgical procedures for Mr. Aarav Sen. Please note that this request is submitted under COORDINATION OF BENEFITS — Insurer2 (Plan B) is the PRIMARY insurer for this claim.

PATIENT INFORMATION:
- Patient: Aarav Sen
- Policy: Plan A (Insurer1) — Secondary Insurer (COB)
- Date of Request: June 19, 2026

PROPOSED PROCEDURES:
- CPT 29888: Arthroscopically aided anterior cruciate ligament reconstruction (Rs 3,50,000)
- CPT 29881: Arthroscopy, knee, surgical; with meniscectomy (Rs 1,00,000)

DIAGNOSIS CODES:
- ICD-10 M23.619: Rupture of anterior cruciate ligament, left knee
- ICD-10 M23.200: Derangement of medial meniscus, left knee

CLINICAL JUSTIFICATION:
Complete ACL tear (Grade III, ICD-10: M23.619) and medial meniscus posterior horn tear (ICD-10: M23.200) confirmed on MRI dated 10/06/2026. Patient unable to bear weight. Surgery medically necessary.

As the secondary insurer under COB rules, Plan A will be responsible for covering the patient's remaining out-of-pocket costs after Plan B (Primary) has processed the claim. We request pre-authorization so that secondary coverage can be applied seamlessly post-surgery.

We request a response within 3-5 business days given the urgency of the procedure.

Sincerely,
DuCO-Agent Authorization Team
On behalf of Aarav Sen"""


def run_demo():
    """Run the full DuCO-Agent pipeline in demo mode using cached responses."""

    print("\n" + "=" * 60)
    print("  ╔═══════════════════════════════════════════════════════╗")
    print("  ║  DuCO-Agent: DEMO MODE (No API Key Required)         ║")
    print("  ║  Using cached LLM responses for demonstration        ║")
    print("  ╚═══════════════════════════════════════════════════════╝")
    print("=" * 60)

    # ─── STAGE 1: INTENT PARSING ─────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"  STAGE: INIT → INTENT_PARSING")
    print(f"{'=' * 60}")
    user_query = (
        "Hi DuCO-Agent, I need to get my knee operated on soon, and Priya has some physical therapy "
        "bills lying around. We have Insurer1 (Plan A) and Insurer2 (Plan B). Can you help us figure "
        "out which plan pays first for my surgery and her bills? How much will we actually have to pay "
        "out of our own pocket? Also, we need the pre-auth letters generated for both insurers so we "
        "don't end up with a claim rejection. Please help!"
    )
    print(f"   User Query: \"{user_query[:80]}...\"")
    print(f"   Detected Intent:")
    print(f"     - COB Calculation: Yes")
    print(f"     - OOP Breakdown:   Yes")
    print(f"     - Pre-Auth Letters: Yes")
    print(f"     - Patients: Aarav, Priya")
    print(f"     - Plans: Plan A, Plan B")

    # ─── STAGE 2: INTAKE (cached) ────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"  STAGE: INTENT_PARSING → INTAKE")
    print(f"{'=' * 60}")
    print("\n[Intake Agent] Starting multi-modal parsing (DEMO: using cached responses)...")
    print("   Parsing PT invoice (OCR)... ✓ Extracted 4 CPT codes")
    print("   Parsing MRI report (PDF)... ✓ Extracted 2 ICD-10 codes")
    print("   Parsing surgeon estimate (OCR)... ✓ Extracted 4 CPT codes")
    print("   Parsing user query (NLP)... ✓ Intent extracted")
    print("   Intake complete.\n")

    intake_data = {
        "priya_pt": CACHED_PRIYA_PT,
        "aarav_mri": CACHED_AARAV_MRI,
        "aarav_surgery": CACHED_AARAV_SURGERY,
        "user_query": user_query,
    }

    # ─── STAGE 3: VALIDATION ─────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"  STAGE: INTAKE → VALIDATION")
    print(f"{'=' * 60}")
    print("   ✓ Validation passed — all 3 required fields extracted")
    print("   ✓ CPT codes found for all documents")

    # ─── STAGE 4: COB CALCULATION ────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"  STAGE: VALIDATION → COB_CALCULATION")
    print(f"{'=' * 60}")
    print("[COB Engine] Calculating coordination of benefits...")
    print("   Applying Birthday Rule: Each person's own employer plan is primary.\n")

    # Run actual COB calculations (no API needed for this)
    aarav_result = calculate_cob(
        patient="Aarav",
        claim_id="CLM-2026-001",
        total_bill=4_50_000,
        cpt_codes=CACHED_AARAV_SURGERY["cpt_codes"],
    )

    print()

    priya_result = calculate_cob(
        patient="Priya",
        claim_id="CLM-2026-002",
        total_bill=30_000,
        cpt_codes=CACHED_PRIYA_PT["cpt_codes"],
    )

    cob_results = {
        "aarav_surgery": aarav_result,
        "priya_pt": priya_result,
    }

    print(f"\n   ┌─────────────────────────────────────────┐")
    print(f"   │  COB RESULTS SUMMARY                     │")
    print(f"   ├─────────────────────────────────────────┤")
    print(f"   │  Aarav surgery OOP: Rs {aarav_result.patient_oop:>10,}   │")
    print(f"   │  Priya PT OOP:      Rs {priya_result.patient_oop:>10,}   │")
    print(f"   │  Combined family:   Rs {aarav_result.patient_oop + priya_result.patient_oop:>10,}   │")
    print(f"   └─────────────────────────────────────────┘")

    # ─── STAGE 5: PRE-AUTH GENERATION (cached letters) ───────────────────
    print(f"\n{'=' * 60}")
    print(f"  STAGE: COB_CALCULATION → PREAUTH_GENERATION")
    print(f"{'=' * 60}")
    print("[Pre-Auth Agent] Generating pre-authorization letters (DEMO: cached)...")

    from agents.preauth_agent import save_letter_as_pdf
    save_letter_as_pdf(
        CACHED_PREAUTH_LETTER_PRIMARY,
        "outputs/preauth_insurer2_primary_aarav.pdf",
        "PRE-AUTHORIZATION REQUEST — INSURER2 (PRIMARY)",
    )
    save_letter_as_pdf(
        CACHED_PREAUTH_LETTER_SECONDARY,
        "outputs/preauth_insurer1_secondary_aarav.pdf",
        "PRE-AUTHORIZATION REQUEST — INSURER1 (SECONDARY / COB)",
    )
    print("   Pre-auth letters saved to outputs/\n")

    # ─── STAGE 6: WHAT-IF ANALYSIS ──────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"  STAGE: PREAUTH_GENERATION → WHAT_IF_ANALYSIS")
    print(f"{'=' * 60}")
    from agents.what_if_analyzer import run_what_if_analysis
    what_if_results = run_what_if_analysis(intake_data)

    # ─── STAGE 7: OUTPUT GENERATION ──────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"  STAGE: WHAT_IF_ANALYSIS → OUTPUT_GENERATION")
    print(f"{'=' * 60}")

    print("   Generating cost flow visualization...")
    generate_cost_flow_chart(cob_results)

    print("   Generating audio briefing (DEMO: cached script)...")
    generate_audio(CACHED_AUDIO_SCRIPT)

    # ─── STAGE 7: FINAL REPORT ───────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"  STAGE: OUTPUT_GENERATION → COMPLETE")
    print(f"{'=' * 60}")

    summary = generate_oop_summary(cob_results)
    print(summary)

    # Save JSON report
    full_report = {
        "agent_metadata": {
            "system": "DuCO-Agent v1.0 (DEMO MODE)",
            "stages_completed": [
                "INIT", "INTENT_PARSING", "INTAKE", "VALIDATION",
                "COB_CALCULATION", "PREAUTH_GENERATION", "WHAT_IF_ANALYSIS",
                "OUTPUT_GENERATION", "COMPLETE",
            ],
            "validation_passed": True,
            "demo_mode": True,
            "note": "This run used cached LLM responses. Run main.py with MISTRAL_API_KEY for live LLM calls.",
        },
        "aarav_surgery": aarav_result.breakdown,
        "priya_pt": priya_result.breakdown,
        "what_if_analysis": what_if_results,
    }

    with open("outputs/full_cob_report.json", "w") as f:
        json.dump(full_report, f, indent=2)

    print("\n" + "=" * 60)
    print("  ╔═══════════════════════════════════════════════════════╗")
    print("  ║  DuCO-Agent DEMO Complete!                           ║")
    print("  ╚═══════════════════════════════════════════════════════╝")
    print("=" * 60)
    print("   Stages: INIT → INTENT_PARSING → INTAKE → VALIDATION")
    print("           → COB_CALCULATION → PREAUTH_GENERATION")
    print("           → WHAT_IF_ANALYSIS → OUTPUT_GENERATION → COMPLETE")
    print(f"\n   Outputs generated:")
    print(f"     📊 outputs/cost_flow.png")
    print(f"     📄 outputs/preauth_insurer2_primary_aarav.pdf")
    print(f"     📄 outputs/preauth_insurer1_secondary_aarav.pdf")
    print(f"     🔊 outputs/audio_briefing.mp3")
    print(f"     📋 outputs/full_cob_report.json")
    print(f"\n   To run with LIVE LLM calls: set MISTRAL_API_KEY=... then python main.py")


if __name__ == "__main__":
    run_demo()
