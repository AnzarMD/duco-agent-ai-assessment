# DuCO-Agent: Dual Coverage Agentic AI System

An intelligent agentic AI system that automates **Coordination of Benefits (COB)** calculations for patients with dual insurance coverage. Built with multi-modal input parsing, LLM-powered medical code extraction, and automated pre-authorization letter generation.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    main.py (Orchestrator)                │
│              DuCOAgentState — State Machine              │
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
└─────────────────────────────────────────────────────────┘
```

## Key Features

- **Multi-Modal Intake**: OCR (Tesseract) for scanned invoices/estimates, pdfplumber for radiology reports, NLP for text queries
- **LLM-Powered Code Extraction**: Claude maps clinical text to CPT/ICD-10 codes
- **COB Logic Engine**: Birthday Rule determination, deductible tracking, coinsurance, OOP max caps
- **Pre-Auth Generation**: AI-drafted clinically accurate authorization letters saved as PDF
- **Visual Outputs**: Cost flow bar charts (matplotlib) and audio briefings (gTTS)
- **Mock Insurance APIs**: FastAPI endpoints simulating insurer plan verification
- **State Machine Design**: Explicit stage transitions with validation loops

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

# Set API key
export ANTHROPIC_API_KEY=sk-ant-...   # Linux/macOS
set ANTHROPIC_API_KEY=sk-ant-...      # Windows
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

### Full Pipeline

```bash
python main.py
```

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
| `outputs/audio_briefing.mp3` | Patient-friendly audio summary |
| `outputs/full_cob_report.json` | Complete COB calculation breakdown |

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

1. **State Machine Pattern**: `DuCOAgentState` with explicit transitions enables retry logic and debugging
2. **Validation Loop**: Intake data is validated before COB calculation proceeds
3. **API Tool-Use**: COB engine calls the mock API to verify rules (demonstrating agentic tool-use)
4. **Fallback OCR**: If Tesseract fails, the system still has structured data from the code mapper
5. **Separation of Concerns**: Each agent handles one responsibility (intake, calculation, letter gen)

## Tech Stack

- **LLM**: Anthropic Claude (claude-sonnet-4-6)
- **OCR**: Tesseract via pytesseract
- **PDF**: pdfplumber (reading), ReportLab (writing)
- **API**: FastAPI + uvicorn
- **Visualization**: matplotlib
- **Audio**: gTTS (Google Text-to-Speech)
- **Testing**: pytest
