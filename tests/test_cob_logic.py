"""
Unit tests for COB Logic Engine.
Validates deductible, coinsurance, OOP max, and primary/secondary determination.
"""

import pytest
from agents.cob_logic_engine import (
    InsurancePlan,
    calculate_cob,
    determine_primary,
    PLAN_A,
    PLAN_B,
)


class TestPrimarySecondaryDetermination:
    """Test Birthday Rule / Employment Rule logic"""

    def test_aarav_primary_is_plan_b(self):
        primary, secondary = determine_primary("Aarav", "surgery")
        assert primary.name == "Plan B"
        assert secondary.name == "Plan A"

    def test_priya_primary_is_plan_a(self):
        primary, secondary = determine_primary("Priya", "surgery")
        assert primary.name == "Plan A"
        assert secondary.name == "Plan B"

    def test_case_insensitive(self):
        primary, _ = determine_primary("aarav", "surgery")
        assert primary.name == "Plan B"

    def test_unknown_patient_raises(self):
        with pytest.raises(ValueError, match="Unknown patient"):
            determine_primary("Unknown", "surgery")


class TestCOBCalculationAarav:
    """Test COB for Aarav's ACL surgery (Rs 4,50,000)"""

    def test_total_does_not_exceed_bill(self):
        result = calculate_cob(
            patient="Aarav",
            claim_id="TEST-001",
            total_bill=4_50_000,
            cpt_codes=[{"code": "29888", "description": "ACL Reconstruction"}],
        )
        total_paid = result.primary_plan_pays + result.secondary_plan_pays + result.patient_oop
        assert total_paid <= result.total_bill

    def test_primary_is_plan_b(self):
        result = calculate_cob(
            patient="Aarav",
            claim_id="TEST-002",
            total_bill=4_50_000,
            cpt_codes=[{"code": "29888", "description": "ACL Reconstruction"}],
        )
        assert result.primary_plan == "Plan B"
        assert result.secondary_plan == "Plan A"

    def test_patient_oop_reasonable(self):
        """Aarav's OOP should be roughly 30k-50k with dual coverage"""
        result = calculate_cob(
            patient="Aarav",
            claim_id="TEST-003",
            total_bill=4_50_000,
            cpt_codes=[{"code": "29888", "description": "ACL Reconstruction"}],
        )
        # With both plans, OOP should be significantly less than bill
        assert result.patient_oop < 100_000
        assert result.patient_oop > 0

    def test_primary_pays_most(self):
        result = calculate_cob(
            patient="Aarav",
            claim_id="TEST-004",
            total_bill=4_50_000,
            cpt_codes=[{"code": "29888", "description": "ACL Reconstruction"}],
        )
        assert result.primary_plan_pays > result.secondary_plan_pays

    def test_breakdown_has_required_keys(self):
        result = calculate_cob(
            patient="Aarav",
            claim_id="TEST-005",
            total_bill=4_50_000,
            cpt_codes=[{"code": "29888", "description": "ACL Reconstruction"}],
        )
        assert "summary" in result.breakdown
        assert "steps" in result.breakdown
        assert len(result.breakdown["steps"]) == 2


class TestCOBCalculationPriya:
    """Test COB for Priya's PT (Rs 30,000)"""

    def test_total_does_not_exceed_bill(self):
        result = calculate_cob(
            patient="Priya",
            claim_id="TEST-PT-001",
            total_bill=30_000,
            cpt_codes=[{"code": "97161", "description": "PT Evaluation"}],
        )
        total_paid = result.primary_plan_pays + result.secondary_plan_pays + result.patient_oop
        assert total_paid <= result.total_bill

    def test_primary_is_plan_a(self):
        result = calculate_cob(
            patient="Priya",
            claim_id="TEST-PT-002",
            total_bill=30_000,
            cpt_codes=[{"code": "97161", "description": "PT Evaluation"}],
        )
        assert result.primary_plan == "Plan A"
        assert result.secondary_plan == "Plan B"

    def test_patient_oop_reasonable(self):
        """Priya's OOP should be roughly 6k-9k with dual coverage"""
        result = calculate_cob(
            patient="Priya",
            claim_id="TEST-PT-003",
            total_bill=30_000,
            cpt_codes=[{"code": "97161", "description": "PT Evaluation"}],
        )
        assert result.patient_oop < 15_000
        assert result.patient_oop > 0


class TestEdgeCases:
    """Test edge cases in COB calculations"""

    def test_zero_bill(self):
        result = calculate_cob(
            patient="Aarav",
            claim_id="TEST-EDGE-001",
            total_bill=0,
            cpt_codes=[],
        )
        assert result.patient_oop == 0
        assert result.primary_plan_pays == 0
        assert result.secondary_plan_pays == 0

    def test_small_bill_below_deductible(self):
        """Bill smaller than primary deductible"""
        result = calculate_cob(
            patient="Aarav",
            claim_id="TEST-EDGE-002",
            total_bill=5_000,
            cpt_codes=[{"code": "99213", "description": "Office visit"}],
        )
        # Bill < Plan B deductible (15000), so primary pays nothing
        assert result.primary_plan_pays == 0
        # Patient owes entire bill to primary deductible
        # Then secondary picks up from there
        total_paid = result.primary_plan_pays + result.secondary_plan_pays + result.patient_oop
        assert total_paid <= 5_000

    def test_bill_equal_to_deductible(self):
        """Bill exactly equals primary deductible"""
        result = calculate_cob(
            patient="Priya",
            claim_id="TEST-EDGE-003",
            total_bill=10_000,
            cpt_codes=[{"code": "97110", "description": "Therapeutic exercise"}],
        )
        # Plan A deductible is 10000, so primary applies full deductible
        total_paid = result.primary_plan_pays + result.secondary_plan_pays + result.patient_oop
        assert total_paid <= 10_000
