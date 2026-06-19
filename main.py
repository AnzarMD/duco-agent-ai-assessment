"""
DuCO-Agent Main Orchestrator
Runs the full agentic pipeline with state management and validation loops.

Usage:
    python main.py
"""

import json
import os

from agents.intake_agent import run_intake_agent
from agents.cob_logic_engine import run_cob_for_all_claims
from agents.preauth_agent import run_preauth_agent
from outputs.output_generator import generate_cost_flow_chart, generate_oop_summary
from outputs.audio_briefing import generate_audio, generate_audio_script

os.makedirs("outputs", exist_ok=True)

MOCK_PATHS = {
    "pt_invoice": "mock_inputs/priya_pt_invoice.png",
    "mri_report": "mock_inputs/aarav_mri_report.pdf",
    "surgeon_estimate": "mock_inputs/surgeon_estimate.jpg",
    "user_query": "mock_inputs/user_query.txt",
}


class DuCOAgentState:
    """Tracks agent state across pipeline stages — state machine pattern"""

    def __init__(self):
        self.stage = "INIT"
        self.intake_data = None
        self.cob_results = None
        self.preauth_letters = None
        self.errors = []
        self.validation_passed = False

    def transition(self, new_stage: str):
        print(f"\n{'=' * 55}")
        print(f"  STATE: {self.stage} -> {new_stage}")
        print(f"{'=' * 55}")
        self.stage = new_stage


def run():
    """Main agentic orchestration loop"""
    state = DuCOAgentState()

    print("\n" + "=" * 55)
    print("  DuCO-Agent: Dual Coverage Agentic AI System")
    print("  Starting pipeline...")
    print("=" * 55)

    # STAGE 1: INTAKE
    state.transition("INTAKE")
    state.intake_data = run_intake_agent(MOCK_PATHS)

    # STAGE 2: VALIDATION LOOP
    state.transition("VALIDATION")
    required_fields = ["priya_pt", "aarav_mri", "aarav_surgery"]
    for field in required_fields:
        if not state.intake_data.get(field):
            state.errors.append(f"Missing intake data: {field}")
    if state.errors:
        print(f"   [ERROR] Validation errors: {state.errors}")
        print("   Pipeline cannot continue. Please check mock inputs.")
        return
    state.validation_passed = True
    print("   Validation passed — all required fields extracted")

    # STAGE 3: COB CALCULATION
    state.transition("COB_CALCULATION")
    state.cob_results = run_cob_for_all_claims(state.intake_data)

    # STAGE 4: PRE-AUTH GENERATION
    state.transition("PREAUTH_GENERATION")
    state.preauth_letters = run_preauth_agent(state.intake_data, state.cob_results)

    # STAGE 5: OUTPUT GENERATION
    state.transition("OUTPUT_GENERATION")
    print("   Generating cost flow visualization...")
    generate_cost_flow_chart(state.cob_results)

    print("   Generating audio briefing...")
    script = generate_audio_script(state.cob_results)
    generate_audio(script)

    # STAGE 6: REPORT
    state.transition("COMPLETE")
    summary = generate_oop_summary(state.cob_results)
    print(summary)

    # Save full JSON output for evaluation
    with open("outputs/full_cob_report.json", "w") as f:
        json.dump(
            {
                "aarav_surgery": state.cob_results["aarav_surgery"].breakdown,
                "priya_pt": state.cob_results["priya_pt"].breakdown,
            },
            f,
            indent=2,
        )

    print("\n" + "=" * 55)
    print("  DuCO-Agent pipeline complete!")
    print("=" * 55)
    print("   Outputs:")
    print("     - outputs/cost_flow.png")
    print("     - outputs/preauth_insurer2_primary_aarav.pdf")
    print("     - outputs/preauth_insurer1_secondary_aarav.pdf")
    print("     - outputs/audio_briefing.mp3")
    print("     - outputs/full_cob_report.json")


if __name__ == "__main__":
    run()
