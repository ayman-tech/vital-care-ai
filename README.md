# Vital AI

> Agentic AI healthcare navigation assistant — medical triage, wellbeing support, and document intelligence in one place.

---

## What is Vital AI?

Vital AI is a skill-based AI assistant that helps users:

- **Understand symptoms** and navigate to the right level of care
- **Decode medical documents** — lab results, prescriptions, referral letters
- **Explain medical jargon** in plain English
- **Prepare for doctor visits** with structured summaries
- **Support student wellbeing** with mood tracking, severity monitoring, and crisis escalation

It is **not** a diagnostic tool. It guides users toward professional care and always includes safety disclaimers.

---

## Folder Structure

```
vital-care/                         ← project root (git repo)
│
├── main.py                         ← convenience launcher (python main.py)
├── pyproject.toml                  ← uv project metadata
├── README.md                       ← this file
│
├── DESIGN.MD                       ← UI design reference
├── WELLBEING_AGENT_SKILL.md        ← wellbeing agent skill specification
├── prompt.md                       ← original backend build spec
│
└── vital-care-backend/             ← ALL application code lives here
    │
    ├── app/
    │   ├── main.py                 ← FastAPI app entry point
    │   ├── config.py               ← env-var settings
    │   │
    │   ├── agents/
    │   │   ├── diagnosis_agent.py  ← DiagnosisChatAgent (orchestrates all skills)
    │   │   └── wellbeing_agent.py  ← WellbeingAgent (mood/tag/severity tracking)
    │   │
    │   ├── skills/                 ← one file per skill
    │   │   ├── symptom_consultation_skill.py
    │   │   ├── urgency_classification_skill.py
    │   │   ├── possible_causes_skill.py
    │   │   ├── temporary_mitigation_skill.py
    │   │   ├── provider_type_skill.py
    │   │   ├── care_locator_skill.py
    │   │   ├── doctor_visit_prep_skill.py
    │   │   ├── medical_document_skill.py
    │   │   └── medical_jargon_skill.py
    │   │
    │   ├── api/routes/             ← FastAPI route handlers
    │   │   ├── diagnosis_chat.py
    │   │   ├── wellbeing_chat.py
    │   │   ├── documents.py
    │   │   ├── medical.py
    │   │   ├── doctor_visit.py
    │   │   └── health.py
    │   │
    │   ├── safety/
    │   │   └── medical_safety_guardrails.py
    │   │
    │   ├── services/
    │   │   ├── llm_service.py
    │   │   ├── rag_service.py
    │   │   ├── document_parser.py
    │   │   ├── location_service.py
    │   │   ├── doctor_document_generator.py
    │   │   └── pdf_generator.py
    │   │
    │   ├── models/                 ← SQLAlchemy ORM models
    │   ├── schemas/                ← Pydantic request/response schemas
    │   ├── prompts/                ← LLM system prompts (one file per skill)
    │   ├── data/
    │   │   └── trusted_sources_seed.json
    │   └── tests/
    │
    ├── templates/
    │   └── index.html              ← Jinja2 UI (served at GET /)
    ├── static/                     ← static assets
    ├── requirements.txt
    ├── .env.example
    └── .env                        ← your local secrets (git-ignored)
```

> **Everything you need to run the app is inside `vital-care-backend/`.**
> The root `main.py` is just a convenience launcher.
> The root `index.html` is an archived standalone prototype — the live UI is `vital-care-backend/templates/index.html`.

---

## Architecture

```
DiagnosisChatAgent
  │
  ├── 1. Safety guardrail scan (regex — before any LLM call)
  ├── 2. Intent detection (LLM)
  ├── 3. Skill dispatch (parallel via asyncio.gather)
  │     ├── SymptomConsultationSkill
  │     ├── UrgencyClassificationSkill  ─┐
  │     ├── PossibleCausesSkill          ├─ parallel
  │     └── ProviderTypeSkill           ─┘
  │         ├── CareLocatorSkill        (depends on ProviderType)
  │         ├── TemporaryMitigationSkill (depends on Urgency)
  │         └── DoctorVisitPrepSkill
  ├── 4. Safety guardrail check on output
  └── 5. Compose structured JSON response

WellbeingAgent
  ├── Consent-first protocol (no tracking without explicit yes)
  ├── LLM call with wellbeing system prompt
  ├── Parse <!--AGENT_DATA--> block (tags, severity, mood/stress scores)
  ├── Session state update (mood history, stress history, tag weights)
  ├── Severity ratchet: LOW → MODERATE → CRITICAL (never downgrades)
  └── On CRITICAL: escalation → PDF report → nearby mental health providers
```

---

## Quick Start

### 1. Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- An OpenAI API key

### 2. Install dependencies

```bash
cd vital-care/vital-care-backend

# With uv
uv pip install -r requirements.txt

# With pip
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Open .env and set your OPENAI_API_KEY
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | ✅ | — | Your OpenAI API key |
| `LLM_MODEL` | | `gpt-4.1-mini` | OpenAI model name |
| `DATABASE_URL` | | `sqlite:///./vitalcare.db` | SQLAlchemy DB URL |
| `VECTOR_DB_PATH` | | `./vector_db` | ChromaDB path (future use) |
| `GOOGLE_MAPS_API_KEY` | | — | Real provider search (future) |

### 4. Run

```bash
# Option A — from vital-care-backend/
uvicorn app.main:app --reload
c
# Option B — from the project root
python main.py

# Option C — custom host/port
python main.py --host=0.0.0.0 --port=8080
```

Open **http://localhost:8000** — the UI loads automatically.

Interactive API docs: **http://localhost:8000/docs**

---

## UI Overview

Single-page Jinja2 template, no build step required.

| Feature | Medical Mode | Mind Mode |
|---|---|---|
| Theme | Light, teal/emerald | Dark, indigo/purple |
| Background | Teal + emerald blobs | Indigo + purple blobs |
| Agent label | CARE TRIAGE AGENT | SAFE SPACE GUIDE |
| Structured cards | Urgency, causes, provider, care | — |
| Sidebar | Hidden | Severity badge, mood graph, tags |
| Panic button | Hidden | Always visible |

The squircle toggle between modes clears chat and starts fresh.
Emergency keywords trigger a full-screen modal instantly (client-side, zero latency).

---

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | UI |
| `GET` | `/health` | Health check |
| `POST` | `/api/diagnosis/chat` | Medical navigation chat |
| `POST` | `/api/wellbeing/chat` | Wellbeing companion chat |
| `POST` | `/api/wellbeing/consent` | Set session consent |
| `POST` | `/api/wellbeing/panic` | Panic button escalation |
| `POST` | `/api/wellbeing/report` | Download PDF session summary |
| `POST` | `/api/documents/upload` | Upload PDF / image / text |
| `POST` | `/api/documents/explain` | Plain-language document explanation |
| `POST` | `/api/medical/explain-term` | Medical jargon explainer |
| `POST` | `/api/doctor-visit/prepare` | Doctor visit prep from session |

### curl Examples

```bash
# Symptom check
curl -X POST http://localhost:8000/api/diagnosis/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I have a severe headache and stiff neck for two days"}'

# Explain a medical term
curl -X POST http://localhost:8000/api/medical/explain-term \
  -H "Content-Type: application/json" \
  -d '{"term": "tachycardia", "context": "found on my ECG report"}'

# Upload a lab result
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@/path/to/labresult.pdf"

# Wellbeing check-in
curl -X POST http://localhost:8000/api/wellbeing/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "yes", "session_id": "your-session-id"}'

# Download wellbeing PDF report
curl -X POST http://localhost:8000/api/wellbeing/report \
  -H "Content-Type: application/json" \
  -d '{"session_id": "your-session-id"}' \
  --output report.pdf
```

---

## Running Tests

```bash
cd vital-care-backend
pytest app/tests/ -v
```

Tests that run without an API key (no real LLM calls):
- Safety guardrail detection (emergency keywords, diagnosis claims)
- Wellbeing consent flow
- Document parser text extraction
- Urgency classification (mocked LLM)
- Wellbeing placeholder endpoints

---

## Safety Design

| Rule | How it is enforced |
|---|---|
| No diagnosis claims | System prompt + regex output scanner |
| No prescription dosing | Prompt instruction + output scanner |
| Emergency override | Regex scan fires before LLM — instant redirect to 911/988 |
| Disclaimer always included | Guardrails append if missing from response |
| Wellbeing crisis resources | Shown immediately at CRITICAL severity |
| Consent-first wellbeing | Zero session tracking without explicit user consent |
| Likelihood not probability | Causes use `more_likely / possible / less_likely / cannot_rule_out` |

> **In a real medical emergency call 911 (US) or your local emergency number.**
> **Mental health crisis: call or text 988 (US) or text HOME to 741741.**

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 · FastAPI · Uvicorn |
| LLM | OpenAI API (gpt-4.1-mini default) |
| Database | SQLite (dev) · SQLAlchemy ORM · Alembic |
| Document parsing | pdfplumber · pypdf · pytesseract |
| PDF generation | fpdf2 |
| Vector search | ChromaDB (wired, not yet populated) |
| Frontend | Jinja2 · Tailwind CSS CDN · Vanilla JS |
| Testing | pytest · pytest-asyncio · httpx |

---

## Roadmap

- [ ] Real user authentication (JWT / OAuth2)
- [ ] Google Maps Places API for real provider search
- [ ] Vector search with ChromaDB + medical source ingestion
- [ ] Wellbeing analytics dashboard
- [ ] Multi-language support
- [ ] Mobile app wrapper
- [ ] HIPAA compliance review before production deployment
- [ ] Alembic database migration scripts
