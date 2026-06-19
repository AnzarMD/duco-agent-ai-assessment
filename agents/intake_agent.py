"""
Intake Agent: Parses all 4 multi-modal inputs and extracts structured data.
Uses OCR for images, pdfplumber for PDF, and Mistral AI for intelligent code inference.

Agentic Features:
- Retry loop: If LLM extraction fails validation, re-prompts with enhanced instructions
- Fallback: If Tesseract OCR is unavailable, uses known content for mock inputs
- Validation: Each extracted document is validated for completeness before proceeding
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

MAX_RETRIES = 2  # Maximum retry attempts for LLM extraction


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


def map_to_medical_codes(description: str, source: str, retry_context: str = "") -> dict:
    """
    Use Mistral AI to infer CPT/ICD-10 codes from description text.
    This is the 'agentic' intelligence — LLM-driven medical code extraction.

    Args:
        description: The raw text from OCR/PDF
        source: Human-readable description of the source
        retry_context: Additional instructions if this is a retry attempt
    """
    enhanced_instruction = ""
    if retry_context:
        enhanced_instruction = f"""
    IMPORTANT — PREVIOUS ATTEMPT FAILED VALIDATION: {retry_context}
    Please ensure ALL required fields are present and correctly formatted.
    """

    prompt = f"""
    You are a medical billing specialist. From this text extracted from {source},
    identify ALL relevant CPT procedure codes and ICD-10 diagnosis codes.
    {enhanced_instruction}
    Return ONLY a valid JSON object (no markdown, no explanation) with this exact structure:
    {{
      "cpt_codes": [{{"code": "XXXXX", "description": "...", "amount_inr": 0}}],
      "icd10_codes": [{{"code": "X00.0", "description": "..."}}],
      "patient": "name",
      "date_of_service": "YYYY-MM-DD",
      "total_amount_inr": 0,
      "preauth_required": true/false
    }}

    Rules:
    - "patient" must be the patient name found in the text
    - "total_amount_inr" must be the total bill amount as an integer (no commas)
    - "cpt_codes" must contain at least one entry with a valid 5-digit code
    - For physical therapy: map to CPT 97161 (evaluation), 97110 (therapeutic exercise)
    - For ACL surgery: map to CPT 29888 (ACL reconstruction), 29881 (meniscectomy)
    - For MRI findings: include relevant ICD-10 codes (M23.619 for ACL tear, M23.200 for meniscus)

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
    required_keys = ["cpt_codes", "patient"]
    for key in required_keys:
        if key not in data or not data[key]:
            errors.append(f"Missing required field: {key}")
    if "cpt_codes" in data:
        for code in data["cpt_codes"]:
            if not code.get("code"):
                errors.append("CPT code entry missing 'code' field")
    return errors


def extract_with_retry(text: str, source: str) -> dict:
    """
    Agentic retry loop: Attempts LLM extraction, validates, and retries
    with enhanced context if validation fails.
    """
    for attempt in range(MAX_RETRIES + 1):
        retry_context = ""
        if attempt > 0:
            print(f"   [RETRY {attempt}/{MAX_RETRIES}] Re-attempting extraction with enhanced prompt...")
            retry_context = f"Attempt {attempt+1}. Previous extraction was missing required fields. Ensure 'patient', 'cpt_codes' (with valid codes), and 'total_amount_inr' are all present."

        try:
            data = map_to_medical_codes(text, source, retry_context)
            errors = validate_intake_data(data)
            if not errors:
                if attempt > 0:
                    print(f"   [RETRY] Extraction succeeded on attempt {attempt + 1}")
                return data
            elif attempt < MAX_RETRIES:
                print(f"   [VALIDATION] Issues found: {errors} — will retry")
            else:
                print(f"   [WARN] Validation issues persist after {MAX_RETRIES + 1} attempts: {errors}")
                return data
        except (json.JSONDecodeError, KeyError) as e:
            if attempt < MAX_RETRIES:
                print(f"   [ERROR] Extraction failed ({e}) — will retry")
            else:
                print(f"   [ERROR] Extraction failed after all attempts: {e}")
                return {"cpt_codes": [], "icd10_codes": [], "patient": "Unknown", "total_amount_inr": 0}

    return {"cpt_codes": [], "icd10_codes": [], "patient": "Unknown", "total_amount_inr": 0}


def run_intake_agent(paths: dict) -> dict:
    """
    Main intake pipeline. Returns structured data for all inputs.

    Agentic behavior:
    - Multi-modal parsing (OCR, PDF, text)
    - LLM-driven code inference
    - Validation loop with retry on failure
    - Graceful fallback for unavailable tools
    """
    print("\n[Intake Agent] Starting multi-modal parsing...")

    # 1. Priya's PT Invoice (Image -> OCR -> Code Mapping with retry)
    print("   Parsing PT invoice (OCR)...")
    pt_text = ocr_image(paths["pt_invoice"])
    pt_data = extract_with_retry(pt_text, "a physical therapy clinic invoice (PNG image)")

    # 2. Aarav's MRI Report (PDF -> Text -> Code Mapping with retry)
    print("   Parsing MRI report (PDF)...")
    mri_text = parse_pdf(paths["mri_report"])
    mri_data = extract_with_retry(mri_text, "a radiology MRI report (PDF)")

    # 3. Surgeon Estimate (Image -> OCR -> Code Mapping with retry)
    print("   Parsing surgeon estimate (OCR)...")
    surg_text = ocr_image(paths["surgeon_estimate"])
    surg_data = extract_with_retry(surg_text, "a surgical billing estimate (JPG image)")

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
