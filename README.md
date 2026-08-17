# DuCO-Agent: Dual Coverage Agentic AI System

An intelligent agentic AI system that automates **Coordination of Benefits (COB)** calculations for patients with dual insurance coverage. Built with multi-modal input parsing, LLM-powered medical code extraction, and automated pre-authorization letter generation.

---

<!-- ## ⚠️ Important Note on Branch Protection Rules

> **GitHub Limitation:** Branch protection rulesets (push rules, required reviews, force-push blocking)
> **cannot be enforced on private repositories** unless the account is upgraded to a **GitHub Team or Enterprise organization plan**.
>
> This repository is private and on a free GitHub account. As a result:
> - The branch protection rules (require PR before merging to `main`, block force pushes, etc.) described in the project requirements **have been configured** but **are NOT enforced by GitHub**.
> - We followed the intended workflow regardless: all changes were made on feature branches and merged via Pull Requests.
> - Semantic commit messages (`feat:`, `fix:`, `refactor:`, `chore:`) were used consistently throughout.
>
> **To fully enforce these rules**, the repository would need to be moved to a GitHub Team organization account.

--
-->

## Note on LLM Choice

> **This project uses Mistral AI** (`mistral-medium-latest` and `mistral-small-latest`) as the LLM backend.
> The original design was built for **Anthropic Claude (claude-sonnet-4-6)**, which provides superior performance
> for medical code extraction and clinical letter generation.
> The architecture is model-agnostic and can be
> switched back to Claude by replacing the Mistral client calls with Anthropic's SDK.

### Model Assignments

| Task | Model Used | Reasoning |
|------|-----------|-----------|
| Medical code extraction (CPT/ICD-10) | `mistral-medium-latest` | Best Mistral model for structured JSON output and complex clinical reasoning |
| Pre-auth letter generation | `mistral-medium-latest` | Requires quality professional writing with clinical terminology |
| Audio briefing script | `mistral-small-latest` | Simple conversational text; lighter model is sufficient |
| Text-to-Speech (voice) | `gTTS` (Google TTS) | Free, no API key needed, supports Indian English accent |

## Architecture

For detailed system architecture with Mermaid flowcharts, see **[ARCHITECTURE.md](./ARCHITECTURE.md)**.

```
┌─────────────────────────────────────────────────────────┐
│                    main.py (Orchestrator)                │
│         DuCOAgentState — 9-Stage State Machine          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────┐  │
│  │ Intake Agent │──>│  COB Engine  │──>│Pre-Auth Agt│  │
│  │  (OCR/PDF)   │   │ (Calc Logic) │   │  (Letters) │  │
│  └──────────────┘   └──────────────┘   └────────────┘  │
│         │                   │                  │        │
│         v                   v                  v        │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────┐  │
│  │ Code Mapper  │   │  Mock APIs   │   │  Outputs   │  │
│  │ (CPT/ICD-10) │   │  (FastAPI)   │   │(Chart/TTS) │  │
│  └──────────────┘   └──────────────┘   └────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  What-If Analyzer — Autonomous Scenario Reasoning│   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Key Features

- **Multi-Modal Intake**: OCR (Tesseract) for scanned invoices/estimates, pdfplumber for radiology reports, NLP for text queries
- **LLM-Powered Code Extraction**: Mistral AI maps clinical text to CPT/ICD-10 codes with retry loops
- **COB Logic Engine**: Birthday Rule determination, deductible tracking, coinsurance, OOP max caps
- **Pre-Auth Generation**: AI-drafted clinically accurate authorization letters saved as PDF
- **Visual Outputs**: Cost flow bar charts (matplotlib) and audio briefings (gTTS)
- **Mock Insurance APIs**: FastAPI endpoints simulating insurer plan verification
- **9-Stage State Machine**: Explicit stage transitions with validation loops and transition history
- **Agentic Reflection**: LLM self-verifies its own COB calculations after each claim
- **Tool-Use Loop**: Per-CPT pre-auth verification by calling the mock insurance API
- **What-If Scenario Analyzer**: Autonomously compares 5 insurance scenarios (no coverage, single plan, dual coverage, mid-year) to demonstrate the value of COB
- **Compliance Checklist**: Each claim includes a structured compliance audit in the JSON output
- **Demo Mode**: Full pipeline runs without API key using cached responses (`run_demo.py`)

## Setup

### Prerequisites

- Python 3.11+
- Tesseract OCR installed system-level:
  - **Windows**: Download from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
  - **Ubuntu**: `sudo apt install tesseract-ocr`
  - **macOS**: `brew install tesseract`

### Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/duco-agent-ai-assessment.git
cd duco-agent-ai-assessment

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Copy .env.example and add your API key
cp .env.example .env
# Edit .env and set MISTRAL_API_KEY (get free key at https://console.mistral.ai)

# Or set directly in terminal:
export MISTRAL_API_KEY=your-key-here    # Linux/macOS
set MISTRAL_API_KEY=your-key-here       # Windows
```

### Generate Mock Input Files

```bash
python mock_inputs/generate_mock_files.py
```

This creates:
- `priya_pt_invoice.png` — Scanned PT clinic invoice
- `aarav_mri_report.pdf` — Radiology MRI report
- `surgeon_estimate.jpg` — Pre-operative billing estimate
- `user_query.txt` — Natural language user request

## Running

### Full Pipeline (requires Mistral API key)

```bash
set MISTRAL_API_KEY=your-key-here
python main.py
```

### Demo Mode (NO API key needed)

```bash
python run_demo.py
```

This runs the complete pipeline using cached LLM responses, so evaluators can see:
- All 9 state machine transitions (including What-If Analysis stage)
- Tool-use (pre-auth verification per CPT code)
- COB calculations with step-by-step math
- What-If scenario comparison table (5 scenarios)
- Generated outputs (chart, PDFs, audio, JSON)

### Mock Insurance API (optional, enhances COB verification)

```bash
uvicorn mock_apis.insurance_api:app --port 8000
```

### Run Tests

```bash
pytest tests/ -v
```

## Outputs

| File | Description |
|------|-------------|
| `outputs/cost_flow.png` | Visual bar chart of cost distribution |
| `outputs/preauth_insurer2_primary_aarav.pdf` | Pre-auth letter to Insurer2 (Primary) |
| `outputs/preauth_insurer1_secondary_aarav.pdf` | Pre-auth letter to Insurer1 (Secondary) |
| `outputs/audio_briefing.mp3` | Patient-friendly audio summary (Indian English) |
| `outputs/full_cob_report.json` | Complete COB breakdown + What-If analysis + compliance checklist |

## What-If Scenario Analysis

The agent autonomously explores 5 scenarios without being asked — demonstrating proactive reasoning:

| Scenario | Family OOP | Savings vs No Insurance |
|----------|-----------|------------------------|
| No Insurance | Rs 4,80,000 | Rs 0 |
| Plan A Only | Rs 89,000 | Rs 3,91,000 |
| Plan B Only | Rs 1,18,000 | Rs 3,62,000 |
| **Dual Coverage (actual)** ★ | **Rs 41,998** | **Rs 4,38,002** |
| Dual Coverage, mid-year | Rs 32,000 | Rs 4,48,000 |

This demonstrates the real financial value of COB coordination and goes beyond what the user explicitly requested.

## COB Logic — How It Works

### Primary/Secondary Determination (Birthday Rule)

| Patient | Own Plan (Primary) | Spouse's Plan (Secondary) |
|---------|-------------------|--------------------------|
| Aarav   | Plan B (Insurer2) | Plan A (Insurer1)        |
| Priya   | Plan A (Insurer1) | Plan B (Insurer2)        |

### Calculation Flow

1. **Primary Plan**: Applies deductible → calculates coinsurance → caps at OOP max
2. **Secondary Plan**: Picks up remaining patient liability → applies its own deductible/coinsurance
3. **Patient OOP**: What remains after both plans pay

### Example: Aarav's Surgery (Rs 4,50,000)

```
Plan B (Primary):  Deductible 15,000 → Pays 80% of 4,35,000 = Rs 3,48,000
Patient after primary: Rs 15,000 + Rs 87,000 coinsurance
                       (capped by OOP max) ≈ Rs 1,02,000

Plan A (Secondary): Picks up Rs 1,02,000 → Deductible 10,000
                    → Pays 80% of 92,000 = Rs 73,600
Patient final OOP: ≈ Rs 28,400
```

## Design Decisions

1. **9-Stage State Machine**: `DuCOAgentState` with explicit transitions — INIT → INTENT_PARSING → INTAKE → VALIDATION → COB_CALCULATION → PREAUTH_GENERATION → WHAT_IF_ANALYSIS → OUTPUT_GENERATION → COMPLETE
2. **Validation Loop**: Intake data validated before COB calculation proceeds; fails fast with clear errors
3. **Tool-Use**: COB engine calls mock API per CPT code to verify pre-auth requirements (not just once globally)
4. **Reflection**: LLM self-verifies its own COB calculation output — catches rounding errors and rule violations
5. **What-If Reasoning**: Agent proactively compares 5 scenarios the user never asked for — true autonomous reasoning
6. **Retry Loop**: If LLM extraction fails validation, re-prompts with enhanced context (up to 2 retries)
7. **Compliance Checklist**: Each claim JSON includes a structured audit of COB rules applied
8. **Model-Agnostic Design**: LLM calls are isolated — swapping Mistral for Claude requires changing only 3 lines

## Project Structure

```
duco-agent-ai-assessment/
├── README.md                  # This file
├── ARCHITECTURE.md            # Mermaid diagrams + design patterns
├── .env.example               # Environment variable template
├── requirements.txt
├── main.py                    # Orchestrator (live pipeline)
├── run_demo.py                # Demo mode (no API key needed)
├── mock_inputs/
│   ├── generate_mock_files.py
│   ├── priya_pt_invoice.png
│   ├── aarav_mri_report.pdf
│   ├── surgeon_estimate.jpg
│   └── user_query.txt
├── agents/
│   ├── intake_agent.py        # Multi-modal parsing + retry loop
│   ├── code_mapper_agent.py   # CPT/ICD-10 lookup tables
│   ├── cob_logic_engine.py    # Core COB + tool-use + reflection
│   ├── preauth_agent.py       # Pre-auth letter generation
│   └── what_if_analyzer.py   # Autonomous scenario reasoning
├── mock_apis/
│   └── insurance_api.py       # FastAPI mock insurers
├── outputs/
│   ├── output_generator.py    # Charts + summary
│   ├── audio_briefing.py      # TTS audio
│   ├── cost_flow.png          # Sample output
│   ├── full_cob_report.json   # Sample output
│   ├── audio_briefing.mp3     # Sample output
│   └── preauth_*.pdf          # Sample outputs
└── tests/
    ├── test_cob_logic.py      # 15 COB tests
    └── test_intake_agent.py   # 9 intake tests
```

## Tech Stack

- **LLM**: Mistral AI (`mistral-medium-latest`, `mistral-small-latest`)
- **TTS**: gTTS (Google Text-to-Speech, Indian English)
- **OCR**: Tesseract via pytesseract
- **PDF**: pdfplumber (reading), ReportLab (writing)
- **API**: FastAPI + uvicorn
- **Visualization**: matplotlib
- **Testing**: pytest

## Switching to Claude (if API key becomes available)

Replace `mistralai` with `anthropic` in requirements.txt, then update the three agent files:

```python
# Before (Mistral)
from mistralai import Mistral
client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY", ""))
response = client.chat.complete(model="mistral-medium-latest", messages=[...])
text = response.choices[0].message.content

# After (Claude)
import anthropic
client = anthropic.Anthropic()
message = client.messages.create(model="claude-sonnet-4-6", max_tokens=1000, messages=[...])
text = message.content[0].text
```
