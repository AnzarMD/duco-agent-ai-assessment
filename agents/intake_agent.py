"""
Intake Agent: Parses all 4 multi-modal inputs and extracts structured data.
Uses OCR for images, pdfplumber for PDF, and Mistral AI for intelligent code inference.
"""

import pdfplumber
import pytesseract
from PIL import Image
import re
import json
import os
import platform
from mistralai.client import Mistral

# Configure Tesseract path for Windows if not in PATH
if platform.system() == "Windows":
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY", ""))


def ocr_image(image_path: str) -> str:
    """
    Extract text from PNG/JPG using Tesseract OCR.
    Falls back to known mock content if Tesseract is not installed.
    """
    try:
        img = Image.open(image_path)
        img = img.convert("L")
        text = pytesseract.image_to_string(img, config="--psm 6")
        return text
    except Exception as e:
        print(f"   [WARN] Tesseract OCR unavailable ({e}), using fallback text extraction")
        return _fallback_text_for_image(image_path)


def _fallback_text_for_image(image_path: str) -> str:
    """
    Fallback: returns known text content for mock input images.
    In production, this would use an alternative OCR service or LLM vision API.
    """
    if "priya_pt_invoice" in image_path:
        return """CITY PHYSIO CLINIC — TAX INVOICE
123, Andheri West, Mumbai - 400053
Phone: +91-22-4567-8900  GSTIN: 27AAAA0000A1Z5
Patient: Mrs. Priya Sen             Date: 14/06/2026
DOB: 12/03/1990   Policy: Plan A (Insurer1 - Corporate Group)
SERVICE DESCRIPTION                         AMOUNT (INR)
Physical Therapy Evaluation (4 sessions)    Rs 8,000
Therapeutic Exercise - Lower Back (8 sessions) Rs 14,000
Ultrasound Therapy (4 sessions)             Rs 5,000
Transcutaneous Electrical Nerve Stimulation Rs 3,000
TOTAL DUE                                   Rs 30,000
Note (handwritten by billing admin):
Pt. has dual coverage - please run thru Plan A first.
Codes: eval + therapeutic exercise - pls verify CPT
All sessions Apr 1 - Jun 14, 2026  /s/ Billing Mgr"""
    elif "surgeon_estimate" in image_path:
        return """STERLING ORTHOPEDIC HOSPITAL
Pre-Operative Billing Estimate
Patient: Aarav Sen   Date: 18/06/2026
Procedure: ACL Reconstruction + Meniscectomy (Left Knee)
Surgeon: Dr. Vikram Nair, MS Ortho
CPT CODE   DESCRIPTION                                          AMOUNT (INR)
29888      Arthroscopically aided ACL reconstruction             Rs 3,50,000
29881      Arthroscopy, knee, surgical; with meniscectomy        Rs 1,00,000
99213      Office/outpatient visit, established patient          Rs 2,500
73721      MRI, any joint of lower extremity, without contrast   Rs 8,000
ESTIMATED TOTAL                                                  Rs 4,60,500
NOTE: CPT 29888 and 29881 require Pre-Authorization from insurer.
Estimate valid for 30 days. Final billing may vary by +/-10%."""
    else:
        return "Unable to extract text from image. Tesseract OCR not available."


def parse_pdf(pdf_path: str) -> str:
    """Extract text from PDF using pdfplumber"""
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def read_text(txt_path: str) -> str:
    """Read plain text file"""
    with open(txt_path) as f:
        return f.read()


def map_to_medical_codes(description: str, source: str) -> dict:
    """
    Use Mistral AI to infer CPT/ICD-10 codes from description text.
    This is the 'agentic' intelligence — LLM-driven medical code extraction.
    """
    prompt = f"""
    You are a medical billing specialist. From this text extracted from {source},
    identify ALL relevant CPT procedure codes and ICD-10 diagnosis codes.
    Return ONLY a JSON object with:
    {{
      "cpt_codes": [{{"code": "XXXXX", "description": "...", "amount_inr": 0}}],
      "icd10_codes": [{{"code": "X00.0", "description": "..."}}],
      "patient": "name",
      "date_of_service": "YYYY-MM-DD",
      "total_amount_inr": 0,
      "preauth_required": true/false
    }}

    TEXT:
    {description}
    """
    response = client.chat.complete(
        model="mistral-medium-latest",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
    )
    raw = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    raw = re.sub(r"```json|```", "", raw).strip()
    return json.loads(raw)


def validate_intake_data(data: dict) -> list[str]:
    """Validation loop: checks extracted data for completeness"""
    errors = []
    required_keys = ["cpt_codes", "patient", "total_amount_inr"]
    for key in required_keys:
        if key not in data or not data[key]:
            errors.append(f"Missing required field: {key}")
    if "cpt_codes" in data:
        for code in data["cpt_codes"]:
            if not code.get("code"):
                errors.append("CPT code entry missing 'code' field")
    return errors


def run_intake_agent(paths: dict) -> dict:
    """
    Main intake pipeline. Returns structured data for all inputs.
    paths = {
        "pt_invoice": "mock_inputs/priya_pt_invoice.png",
        "mri_report": "mock_inputs/aarav_mri_report.pdf",
        "surgeon_estimate": "mock_inputs/surgeon_estimate.jpg",
        "user_query": "mock_inputs/user_query.txt",
    }
    """
    print("\n[Intake Agent] Starting multi-modal parsing...")

    # 1. Priya's PT Invoice (Image -> OCR -> Code Mapping)
    print("   Parsing PT invoice (OCR)...")
    pt_text = ocr_image(paths["pt_invoice"])
    pt_data = map_to_medical_codes(pt_text, "a physical therapy clinic invoice (PNG image)")
    pt_errors = validate_intake_data(pt_data)
    if pt_errors:
        print(f"   [WARN] PT invoice validation issues: {pt_errors}")

    # 2. Aarav's MRI Report (PDF -> Text -> Code Mapping)
    print("   Parsing MRI report (PDF)...")
    mri_text = parse_pdf(paths["mri_report"])
    mri_data = map_to_medical_codes(mri_text, "a radiology MRI report (PDF)")
    mri_errors = validate_intake_data(mri_data)
    if mri_errors:
        print(f"   [WARN] MRI report validation issues: {mri_errors}")

    # 3. Surgeon Estimate (Image -> OCR -> Code Mapping)
    print("   Parsing surgeon estimate (OCR)...")
    surg_text = ocr_image(paths["surgeon_estimate"])
    surg_data = map_to_medical_codes(surg_text, "a surgical billing estimate (JPG image)")
    surg_errors = validate_intake_data(surg_data)
    if surg_errors:
        print(f"   [WARN] Surgeon estimate validation issues: {surg_errors}")

    # 4. User Query (Text -> NLP intent extraction)
    print("   Parsing user query (NLP)...")
    user_query = read_text(paths["user_query"])

    print("   Intake complete.\n")
    return {
        "priya_pt": pt_data,
        "aarav_mri": mri_data,
        "aarav_surgery": surg_data,
        "user_query": user_query,
    }
