"""
Pre-Authorization Letter Generator

Produces professional, clinically accurate letters for Insurer1 and Insurer2.
Uses Mistral AI to draft clinically sound pre-auth requests.
"""

import os
from mistralai.client import Mistral
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import date
import textwrap

client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY", ""))


def generate_preauth_letter(
    insurer_name: str,
    patient_name: str,
    cpt_codes: list[dict],
    icd10_codes: list[dict],
    clinical_justification: str,
    is_primary: bool,
) -> str:
    """Use Mistral AI to draft a clinically sound pre-auth letter"""
    cpt_str = "\n".join(
        f"  - CPT {c['code']}: {c['description']} ({c.get('amount_inr', 0):,} INR)"
        for c in cpt_codes
    )
    icd_str = "\n".join(
        f"  - ICD-10 {c['code']}: {c['description']}" for c in icd10_codes
    )

    prompt = f"""
    You are a medical authorization specialist. Write a formal pre-authorization request letter to {insurer_name}
    for the following procedure. The letter should be:
    - Professionally formatted with a date, subject line, and salutation
    - Clinically justified using the MRI findings provided
    - Include all CPT codes and ICD-10 codes
    - Reference that this is the {"PRIMARY" if is_primary else "SECONDARY (coordination of benefits)"} insurer
    - Mention the urgency of the procedure
    - Request a response within 3-5 business days
    - No more than 400 words

    Patient: {patient_name}
    Policy: {"Plan B" if "Insurer2" in insurer_name else "Plan A"}
    Date of Request: {date.today().strftime("%B %d, %Y")}

    CPT Codes:
    {cpt_str}

    ICD-10 Diagnosis Codes:
    {icd_str}

    Clinical Justification:
    {clinical_justification}
    """
    response = client.chat.complete(
        model="mistral-medium-latest",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
    )
    return response.choices[0].message.content


def save_letter_as_pdf(letter_text: str, output_path: str, title: str):
    """Save the generated letter as a PDF"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    c = canvas.Canvas(output_path, pagesize=A4)
    W, H = A4
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, H - 50, title)
    c.setFont("Helvetica", 10)
    y = H - 80
    for line in letter_text.split("\n"):
        for wrapped in textwrap.wrap(line, width=95) or [""]:
            c.drawString(50, y, wrapped)
            y -= 14
            if y < 60:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = H - 50
    c.save()


def run_preauth_agent(intake_data: dict, cob_results: dict) -> dict:
    """Generate pre-auth letters for both insurers"""
    print("[Pre-Auth Agent] Generating pre-authorization letters...")

    mri_findings = (
        "Complete ACL tear (Grade III, ICD-10: M23.619) and medial meniscus posterior "
        "horn tear (ICD-10: M23.200) confirmed on MRI dated 10/06/2026. Patient unable "
        "to bear weight. Surgery medically necessary."
    )
    cpt_surgery = cob_results["aarav_surgery"].breakdown["cpt_codes"]
    icd_surgery = [
        {"code": "M23.619", "description": "Rupture of anterior cruciate ligament, left knee"},
        {"code": "M23.200", "description": "Derangement of medial meniscus, left knee"},
    ]

    # Letter to Insurer2 (Plan B — PRIMARY for Aarav)
    letter_insurer2 = generate_preauth_letter(
        insurer_name="Insurer2 (Plan B)",
        patient_name="Aarav Sen",
        cpt_codes=cpt_surgery,
        icd10_codes=icd_surgery,
        clinical_justification=mri_findings,
        is_primary=True,
    )
    save_letter_as_pdf(
        letter_insurer2,
        "outputs/preauth_insurer2_primary_aarav.pdf",
        "PRE-AUTHORIZATION REQUEST — INSURER2 (PRIMARY)",
    )

    # Letter to Insurer1 (Plan A — SECONDARY for Aarav)
    letter_insurer1 = generate_preauth_letter(
        insurer_name="Insurer1 (Plan A)",
        patient_name="Aarav Sen",
        cpt_codes=cpt_surgery,
        icd10_codes=icd_surgery,
        clinical_justification=mri_findings,
        is_primary=False,
    )
    save_letter_as_pdf(
        letter_insurer1,
        "outputs/preauth_insurer1_secondary_aarav.pdf",
        "PRE-AUTHORIZATION REQUEST — INSURER1 (SECONDARY / COB)",
    )

    print("   Pre-auth letters saved to outputs/\n")
    return {
        "insurer2_letter": letter_insurer2,
        "insurer1_letter": letter_insurer1,
    }
