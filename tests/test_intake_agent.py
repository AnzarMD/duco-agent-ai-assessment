"""
Unit tests for the Intake Agent.
Tests OCR, PDF parsing, and text reading without needing the Claude API.
"""

import os
import shutil
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image

from agents.intake_agent import ocr_image, parse_pdf, read_text, validate_intake_data

# Check if Tesseract is installed
TESSERACT_AVAILABLE = shutil.which("tesseract") is not None


class TestOCRImage:
    """Test image OCR functionality"""

    @pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="Tesseract not installed")
    def test_ocr_returns_string(self, tmp_path):
        """OCR should return a string from a valid image"""
        # Create a simple test image
        img = Image.new("RGB", (200, 100), color=(255, 255, 255))
        img_path = str(tmp_path / "test.png")
        img.save(img_path)

        result = ocr_image(img_path)
        assert isinstance(result, str)

    @pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="Tesseract not installed")
    def test_ocr_handles_blank_image(self, tmp_path):
        """OCR on blank image should return empty-ish string"""
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        img_path = str(tmp_path / "blank.png")
        img.save(img_path)

        result = ocr_image(img_path)
        assert isinstance(result, str)


class TestParsePDF:
    """Test PDF text extraction"""

    def test_parse_pdf_extracts_text(self, tmp_path):
        """Should extract text from a simple PDF"""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4

        pdf_path = str(tmp_path / "test.pdf")
        c = canvas.Canvas(pdf_path, pagesize=A4)
        c.drawString(100, 700, "Test medical report content")
        c.save()

        result = parse_pdf(pdf_path)
        assert "Test medical report content" in result

    def test_parse_pdf_returns_string(self, tmp_path):
        """Should always return a string"""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4

        pdf_path = str(tmp_path / "empty.pdf")
        c = canvas.Canvas(pdf_path, pagesize=A4)
        c.save()

        result = parse_pdf(pdf_path)
        assert isinstance(result, str)


class TestReadText:
    """Test text file reading"""

    def test_read_text_returns_content(self, tmp_path):
        txt_path = str(tmp_path / "test.txt")
        with open(txt_path, "w") as f:
            f.write("Hello DuCO-Agent")

        result = read_text(txt_path)
        assert result == "Hello DuCO-Agent"


class TestValidateIntakeData:
    """Test intake data validation"""

    def test_valid_data_passes(self):
        data = {
            "cpt_codes": [{"code": "29888", "description": "ACL"}],
            "patient": "Aarav",
            "total_amount_inr": 450000,
        }
        errors = validate_intake_data(data)
        assert errors == []

    def test_missing_patient_fails(self):
        data = {
            "cpt_codes": [{"code": "29888", "description": "ACL"}],
            "total_amount_inr": 450000,
        }
        errors = validate_intake_data(data)
        assert any("patient" in e for e in errors)

    def test_empty_cpt_codes_fails(self):
        data = {
            "cpt_codes": [],
            "patient": "Aarav",
            "total_amount_inr": 450000,
        }
        errors = validate_intake_data(data)
        assert any("cpt_codes" in e for e in errors)

    def test_missing_code_field_in_cpt(self):
        data = {
            "cpt_codes": [{"description": "ACL"}],  # missing 'code'
            "patient": "Aarav",
            "total_amount_inr": 450000,
        }
        errors = validate_intake_data(data)
        assert any("code" in e for e in errors)
