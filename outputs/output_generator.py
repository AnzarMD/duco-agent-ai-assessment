"""
Generates the visual cost breakdown chart using matplotlib.
Shows how the total bill flows between insurers and patient OOP.
"""

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for file output
import matplotlib.pyplot as plt
import os


def generate_cost_flow_chart(cob_results: dict, output_path: str = "outputs/cost_flow.png"):
    """Generate a dual bar chart showing cost flow for both patients"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    fig.suptitle(
        "DuCO-Agent — Dual Coverage Cost Flow Analysis",
        fontsize=14,
        fontweight="bold",
    )

    # Aarav's Surgery
    ax1 = axes[0]
    aarav = cob_results["aarav_surgery"]
    b = aarav.breakdown["summary"]
    labels = ["Plan B\n(Primary)", "Plan A\n(Secondary)", "Aarav's\nOut-of-Pocket"]
    values = [b["primary_pays_inr"], b["secondary_pays_inr"], b["patient_final_oop_inr"]]
    colors = ["#2196F3", "#4CAF50", "#FF5722"]
    bars = ax1.bar(labels, values, color=colors, width=0.5, edgecolor="white", linewidth=1.5)
    ax1.set_title(f"Aarav's ACL Surgery — Total: Rs {aarav.total_bill:,}", fontsize=11)
    ax1.set_ylabel("Amount (INR)")
    ax1.set_ylim(0, max(values) * 1.3)
    for bar, val in zip(bars, values):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 3000,
            f"Rs {val:,}",
            ha="center",
            fontsize=9,
            fontweight="bold",
        )
    ax1.spines[["top", "right"]].set_visible(False)

    # Priya's PT
    ax2 = axes[1]
    priya = cob_results["priya_pt"]
    p = priya.breakdown["summary"]
    labels2 = ["Plan A\n(Primary)", "Plan B\n(Secondary)", "Priya's\nOut-of-Pocket"]
    values2 = [p["primary_pays_inr"], p["secondary_pays_inr"], p["patient_final_oop_inr"]]
    bars2 = ax2.bar(labels2, values2, color=colors, width=0.5, edgecolor="white", linewidth=1.5)
    ax2.set_title(f"Priya's PT Sessions — Total: Rs {priya.total_bill:,}", fontsize=11)
    ax2.set_ylabel("Amount (INR)")
    ax2.set_ylim(0, max(values2) * 1.3 if max(values2) > 0 else 1000)
    for bar, val in zip(bars2, values2):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 500,
            f"Rs {val:,}",
            ha="center",
            fontsize=9,
            fontweight="bold",
        )
    ax2.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"   Cost flow chart saved to {output_path}")


def generate_oop_summary(cob_results: dict) -> str:
    """Generate a formatted text summary of OOP costs"""
    aarav = cob_results["aarav_surgery"]
    priya = cob_results["priya_pt"]
    total_oop = aarav.patient_oop + priya.patient_oop
    total_bills = aarav.total_bill + priya.total_bill
    savings = total_bills - total_oop

    return f"""
    ╔══════════════════════════════════════════════════════════╗
    ║       DuCO-AGENT — FINANCIAL SUMMARY (INR)              ║
    ╠══════════════════════════════════════════════════════════╣
    ║                                                          ║
    ║  AARAV SEN — ACL Surgery (CPT 29888 + 29881)            ║
    ║    Total Bill:              Rs {aarav.total_bill:>10,}            ║
    ║    Plan B pays (Primary):   Rs {aarav.primary_plan_pays:>10,}            ║
    ║    Plan A pays (Secondary): Rs {aarav.secondary_plan_pays:>10,}            ║
    ║    Aarav's Out-of-Pocket:   Rs {aarav.patient_oop:>10,}            ║
    ║                                                          ║
    ║  PRIYA SEN — Physical Therapy (CPT 97161 + 97110)       ║
    ║    Total Bill:              Rs {priya.total_bill:>10,}            ║
    ║    Plan A pays (Primary):   Rs {priya.primary_plan_pays:>10,}            ║
    ║    Plan B pays (Secondary): Rs {priya.secondary_plan_pays:>10,}            ║
    ║    Priya's Out-of-Pocket:   Rs {priya.patient_oop:>10,}            ║
    ║                                                          ║
    ║  COMBINED SUMMARY                                        ║
    ║    Total Bills:             Rs {total_bills:>10,}            ║
    ║    Total Saved via COB:     Rs {savings:>10,}            ║
    ║    Combined Family OOP:     Rs {total_oop:>10,}            ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
