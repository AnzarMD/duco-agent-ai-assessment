"""
Code Mapper Agent: CPT/ICD-10 mapping utilities.
Provides lookup tables and validation for medical billing codes
used throughout the DuCO-Agent system.
"""

# Standard CPT code mappings for orthopedic and PT procedures
CPT_CODES = {
    "29888": {
        "description": "Arthroscopically aided anterior cruciate ligament repair/augmentation or reconstruction",
        "category": "Surgery",
        "preauth_required": True,
    },
    "29881": {
        "description": "Arthroscopy, knee, surgical; with meniscectomy including any meniscal shaving",
        "category": "Surgery",
        "preauth_required": True,
    },
    "97161": {
        "description": "Physical therapy evaluation, low complexity",
        "category": "Physical Therapy",
        "preauth_required": False,
    },
    "97110": {
        "description": "Therapeutic procedure, therapeutic exercises to develop strength and endurance",
        "category": "Physical Therapy",
        "preauth_required": False,
    },
    "97035": {
        "description": "Ultrasound, each 15 minutes",
        "category": "Physical Therapy",
        "preauth_required": False,
    },
    "97032": {
        "description": "Electrical stimulation (manual), each 15 minutes",
        "category": "Physical Therapy",
        "preauth_required": False,
    },
    "99213": {
        "description": "Office or other outpatient visit, established patient, low to moderate complexity",
        "category": "E&M",
        "preauth_required": False,
    },
    "73721": {
        "description": "MRI, any joint of lower extremity, without contrast material",
        "category": "Radiology",
        "preauth_required": True,
    },
}

# ICD-10 diagnosis code mappings
ICD10_CODES = {
    "M23.619": {
        "description": "Other spontaneous disruption of anterior cruciate ligament of unspecified knee",
        "category": "Knee - Ligament",
    },
    "M23.200": {
        "description": "Derangement of unspecified medial meniscus due to old tear or injury, unspecified knee",
        "category": "Knee - Meniscus",
    },
    "M54.5": {
        "description": "Low back pain",
        "category": "Spine",
    },
    "M25.562": {
        "description": "Pain in left knee",
        "category": "Knee - Pain",
    },
}


def validate_cpt_code(code: str) -> dict | None:
    """Validate and return CPT code details, or None if invalid"""
    return CPT_CODES.get(code)


def validate_icd10_code(code: str) -> dict | None:
    """Validate and return ICD-10 code details, or None if invalid"""
    return ICD10_CODES.get(code)


def is_preauth_required(cpt_code: str) -> bool:
    """Check if a CPT code requires pre-authorization"""
    info = CPT_CODES.get(cpt_code, {})
    return info.get("preauth_required", False)


def get_codes_for_acl_reconstruction() -> dict:
    """Standard code set for ACL reconstruction procedure"""
    return {
        "cpt_codes": [
            {"code": "29888", "description": CPT_CODES["29888"]["description"]},
            {"code": "29881", "description": CPT_CODES["29881"]["description"]},
        ],
        "icd10_codes": [
            {"code": "M23.619", "description": ICD10_CODES["M23.619"]["description"]},
            {"code": "M23.200", "description": ICD10_CODES["M23.200"]["description"]},
        ],
    }


def get_codes_for_physical_therapy() -> dict:
    """Standard code set for physical therapy sessions"""
    return {
        "cpt_codes": [
            {"code": "97161", "description": CPT_CODES["97161"]["description"]},
            {"code": "97110", "description": CPT_CODES["97110"]["description"]},
            {"code": "97035", "description": CPT_CODES["97035"]["description"]},
            {"code": "97032", "description": CPT_CODES["97032"]["description"]},
        ],
        "icd10_codes": [
            {"code": "M54.5", "description": ICD10_CODES["M54.5"]["description"]},
        ],
    }
