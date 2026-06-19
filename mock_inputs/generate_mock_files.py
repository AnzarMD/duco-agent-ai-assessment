"""
Generates all 4 mock input files for DuCO-Agent.
Run once: python mock_inputs/generate_mock_files.py
"""

from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import random
import os

OUT = os.path.dirname(os.path.abspath(__file__))


def generate_priya_pt_invoice():
    """Scanned-style invoice with handwritten-looking notes"""
    img = Image.new("RGB", (800, 600), color=(252, 248, 240))
    draw = ImageDraw.Draw(img)

    # Add slight texture / crumple effect (random noise)
    for _ in range(3000):
        x, y = random.randint(0, 799), random.randint(0, 599)
        v = random.randint(200, 240)
        img.putpixel((x, y), (v, v - 5, v - 10))

    draw.rectangle([30, 30, 770, 570], outline=(100, 80, 60), width=2)
    draw.text((40, 45), "CITY PHYSIO CLINIC — TAX INVOICE", fill=(30, 30, 100))
    draw.text((40, 70), "123, Andheri West, Mumbai - 400053", fill=(60, 60, 60))
    draw.text((40, 90), "Phone: +91-22-4567-8900  GSTIN: 27AAAA0000A1Z5", fill=(60, 60, 60))
    draw.line([30, 110, 770, 110], fill=(150, 150, 150))
    draw.text((40, 125), "Patient: Mrs. Priya Sen             Date: 14/06/2026", fill=(0, 0, 0))
    draw.text((40, 150), "DOB: 12/03/1990   Policy: Plan A (Insurer1 - Corporate Group)", fill=(0, 0, 0))
    draw.line([30, 175, 770, 175], fill=(200, 200, 200))
    draw.text((40, 190), "SERVICE DESCRIPTION", fill=(0, 0, 100))
    draw.text((500, 190), "AMOUNT (INR)", fill=(0, 0, 100))
    rows = [
        ("Physical Therapy Evaluation (4 sessions)", "Rs 8,000"),
        ("Therapeutic Exercise - Lower Back (8 sessions)", "Rs 14,000"),
        ("Ultrasound Therapy (4 sessions)", "Rs 5,000"),
        ("Transcutaneous Electrical Nerve Stimulation", "Rs 3,000"),
    ]
    y = 215
    for desc, amt in rows:
        draw.text((40, y), desc, fill=(30, 30, 30))
        draw.text((550, y), amt, fill=(30, 30, 30))
        y += 28
    draw.line([30, y + 5, 770, y + 5], fill=(100, 100, 100), width=2)
    draw.text((40, y + 15), "TOTAL DUE", fill=(0, 0, 0))
    draw.text((520, y + 15), "Rs 30,000", fill=(180, 0, 0))
    # Handwritten-style annotation
    draw.text((40, y + 55), "* Note (handwritten by billing admin):", fill=(0, 100, 0))
    draw.text((40, y + 75), "  Pt. has dual coverage - please run thru Plan A first.", fill=(0, 100, 0))
    draw.text((40, y + 95), "  Codes: eval + therapeutic exercise - pls verify CPT", fill=(0, 100, 0))
    draw.text((40, y + 115), "  All sessions Apr 1 - Jun 14, 2026  /s/ Billing Mgr", fill=(0, 100, 0))

    img.save(os.path.join(OUT, "priya_pt_invoice.png"))
    print("priya_pt_invoice.png created")


def generate_aarav_mri_report():
    """PDF MRI radiology report with clinical language"""
    path = os.path.join(OUT, "aarav_mri_report.pdf")
    c = canvas.Canvas(path, pagesize=A4)
    W, H = A4
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, H - 50, "RADIOLOGY REPORT — MRI LEFT KNEE")
    c.setFont("Helvetica", 10)
    c.drawString(50, H - 70, "Apollo Imaging Centre, Mumbai")
    c.drawString(50, H - 85, "Report Date: 10/06/2026    Accession: MRI-2026-KN-7742")
    c.drawString(50, H - 100, "Patient: Aarav Sen    DOB: 05/08/1988    Gender: Male")
    c.drawString(50, H - 115, "Referring Physician: Dr. Ramesh Iyer, Orthopaedic Surgery")
    c.drawString(50, H - 130, "Clinical History: Sports injury during cricket match. Pain, swelling, inability to bear weight.")
    c.line(50, H - 140, W - 50, H - 140)

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, H - 160, "TECHNIQUE:")
    c.setFont("Helvetica", 10)
    c.drawString(50, H - 175, "MRI of the left knee performed on 1.5T scanner. Sagittal, coronal, axial sequences obtained.")

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, H - 200, "FINDINGS:")
    c.setFont("Helvetica", 10)
    findings = [
        "ANTERIOR CRUCIATE LIGAMENT (ACL): Complete tear of the anterior cruciate ligament (ACL) is",
        "identified. The ligament fibres are discontinuous with complete disruption at the mid-substance.",
        "There is posterior tibial translation consistent with ACL insufficiency. Grade III tear.",
        "",
        "MEDIAL MENISCUS: Horizontal cleavage tear is identified involving the posterior horn of the",
        "medial meniscus, extending to the inferior articular surface. ICD-10: M23.200.",
        "",
        "LATERAL MENISCUS: Intact. No significant abnormality.",
        "",
        "ARTICULAR CARTILAGE: Mild grade I-II chondromalacia noted at the medial femoral condyle.",
        "",
        "LIGAMENTS: Intact PCL, LCL, and MCL. No collateral ligament injury identified.",
        "",
        "JOINT EFFUSION: Moderate joint effusion present in the suprapatellar pouch.",
        "",
        "BONE: No fracture, bone contusion, or osseous lesion identified.",
    ]
    y_pos = H - 215
    for line in findings:
        c.drawString(50, y_pos, line)
        y_pos -= 15

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y_pos - 10, "IMPRESSION:")
    c.setFont("Helvetica", 10)
    impressions = [
        "1. Complete ACL tear (Grade III) — ICD-10: M23.619",
        "2. Medial meniscus posterior horn tear — ICD-10: M23.200",
        "3. Moderate joint effusion",
        "",
        "Clinical correlation recommended. Surgical consultation advised.",
        "",
        "Reported by: Dr. Sunita Patel, MD (Radiology)    Signed: 10/06/2026 14:32 IST",
    ]
    y_pos -= 25
    for line in impressions:
        c.drawString(50, y_pos, line)
        y_pos -= 15

    c.save()
    print("aarav_mri_report.pdf created")


def generate_surgeon_estimate():
    """Billing estimate as JPG image"""
    img = Image.new("RGB", (800, 500), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 780, 480], outline=(0, 0, 0), width=2)
    draw.text((40, 35), "STERLING ORTHOPEDIC HOSPITAL", fill=(0, 0, 100))
    draw.text((40, 55), "Pre-Operative Billing Estimate", fill=(50, 50, 50))
    draw.text((40, 75), "Patient: Aarav Sen   Date: 18/06/2026", fill=(0, 0, 0))
    draw.text((40, 95), "Procedure: ACL Reconstruction + Meniscectomy (Left Knee)", fill=(0, 0, 0))
    draw.text((40, 115), "Surgeon: Dr. Vikram Nair, MS Ortho", fill=(0, 0, 0))
    draw.line([20, 135, 780, 135], fill=(0, 0, 0), width=2)
    draw.text((40, 145), "CPT CODE", fill=(0, 0, 100))
    draw.text((200, 145), "DESCRIPTION", fill=(0, 0, 100))
    draw.text((580, 145), "AMOUNT (INR)", fill=(0, 0, 100))
    draw.line([20, 165, 780, 165], fill=(150, 150, 150))
    rows = [
        ("29888", "Arthroscopically aided ACL reconstruction", "Rs 3,50,000"),
        ("", "  (with or without other procedures)", ""),
        ("29881", "Arthroscopy, knee, surgical; with meniscectomy", "Rs 1,00,000"),
        ("99213", "Office/outpatient visit, established patient", "Rs  2,500"),
        ("73721", "MRI, any joint of lower extremity, without contrast", "Rs  8,000"),
    ]
    y = 180
    for code, desc, amt in rows:
        draw.text((40, y), code, fill=(0, 80, 0))
        draw.text((200, y), desc, fill=(30, 30, 30))
        if amt:
            draw.text((580, y), amt, fill=(30, 30, 30))
        y += 22
    draw.line([20, y + 5, 780, y + 5], fill=(0, 0, 0), width=2)
    draw.text((40, y + 15), "ESTIMATED TOTAL", fill=(0, 0, 0))
    draw.text((560, y + 15), "Rs 4,60,500", fill=(180, 0, 0))
    draw.text((40, y + 45), "NOTE: CPT 29888 and 29881 require Pre-Authorization from insurer.", fill=(100, 0, 0))
    draw.text((40, y + 65), "Estimate valid for 30 days. Final billing may vary by +/-10%.", fill=(80, 80, 80))
    img.save(os.path.join(OUT, "surgeon_estimate.jpg"), quality=85)
    print("surgeon_estimate.jpg created")


def generate_user_query():
    text = (
        "Hi DuCO-Agent, I need to get my knee operated on soon, and Priya has some physical therapy "
        "bills lying around. We have Insurer1 (Plan A) and Insurer2 (Plan B). Can you help us figure "
        "out which plan pays first for my surgery and her bills? How much will we actually have to pay "
        "out of our own pocket? Also, we need the pre-auth letters generated for both insurers so we "
        "don't end up with a claim rejection. Please help!"
    )
    with open(os.path.join(OUT, "user_query.txt"), "w") as f:
        f.write(text)
    print("user_query.txt created")


if __name__ == "__main__":
    generate_priya_pt_invoice()
    generate_aarav_mri_report()
    generate_surgeon_estimate()
    generate_user_query()
    print("\nAll mock inputs generated in mock_inputs/")
