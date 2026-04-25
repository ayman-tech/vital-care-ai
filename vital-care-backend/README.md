# Vital AI Backend

Agentic AI healthcare navigation assistant backend built with FastAPI and OpenAI.

---

## Overview

Vital AI is a medical navigation assistant that helps users understand their symptoms, navigate to appropriate care, explain medical documents, and prepare for doctor visits. It is **not** a diagnostic tool and does not replace professional medical advice.

The backend uses a **skill-based agent architecture**: one central `DiagnosisChatAgent` detects user intent and orchestrates a set of specialized skills to compose a structured, safety-checked response.

---

## Architecture

```
DiagnosisChatAgent
  ├── SymptomConsultationSkill     — extract and structure symptom details
  ├── UrgencyClassificationSkill  — classify urgency level (emergency → self_care)
  ├── PossibleCausesSkill          — suggest possible (non-diagnostic) causes
  ├── TemporaryMitigationSkill     — safe home care steps while awaiting care
  ├── ProviderTypeSkill            — recommend appropriate provider type
  ├── CareLocatorSkill             — find nearby care (mock; Google Maps ready)
  ├── DoctorVisitPrepSkill         — generate structured visit preparation
  ├── MedicalDocumentSkill         — explain medical documents in plain English
  └── MedicalJargonSkill           — explain medical terminology
```

Each skill is a focused, independently testable unit. The agent runs skills in parallel where possible using `asyncio.gather`.

**Safety guardrails** run before and after LLM calls:
- Emergency red-flag detection (regex + LLM)
- Diagnosis claim prevention
- Unsafe medication advice detection
- Disclaimer enforcement

---

## Setup

### Prerequisites

- Python 3.11+
- An OpenAI API key

### Installation

```bash
cd vital-care-backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key (required) |
| `DATABASE_URL` | SQLAlchemy DB URL (default: SQLite) |
| `LLM_MODEL` | OpenAI model to use (default: `gpt-4.1-mini`) |
| `VECTOR_DB_PATH` | Path for vector DB storage (future use) |
| `GOOGLE_MAPS_API_KEY` | For real provider search (future use) |

---

## Running the Server

```bash
uvicorn app.main:app --reload
```

Server runs at: `http://localhost:8000`

API docs (Swagger UI): `http://localhost:8000/docs`

---

## API Endpoints

### Health Check

```
GET /health
```

### Diagnosis Chat

```
POST /api/diagnosis/chat
```

**Request:**
```json
{
  "user_id": "optional-user-id",
  "session_id": "optional-session-id",
  "message": "I have a headache and neck stiffness for 2 days",
  "location": {
    "city": "Chicago",
    "state": "IL",
    "country": "US"
  },
  "user_context": {
    "age": 32,
    "sex": "female",
    "pregnant": false,
    "known_conditions": ["migraines"],
    "medications": ["ibuprofen"],
    "allergies": ["penicillin"]
  }
}
```

**Response:** Structured JSON with urgency, possible causes, mitigation steps, provider recommendation, care suggestions, and visit prep document.

---

### Document Upload

```
POST /api/documents/upload
Content-Type: multipart/form-data
```

**Supported file types:** PDF, PNG, JPEG, TIFF, BMP, GIF, WEBP, TXT

**Response:**
```json
{
  "document_id": "uuid",
  "filename": "bloodwork.pdf",
  "extracted_text_preview": "Complete Blood Count...",
  "status": "processed"
}
```

---

### Document Explanation

```
POST /api/documents/explain
```

**Request:**
```json
{
  "document_id": "uuid-from-upload",
  "user_context": { "age": 45, "sex": "male" }
}
```

---

### Medical Term Explanation

```
POST /api/medical/explain-term
```

**Request:**
```json
{
  "term": "hemoglobin A1c",
  "context": "Found on my diabetes lab report"
}
```

---

### Doctor Visit Preparation

```
POST /api/doctor-visit/prepare
```

**Request:**
```json
{
  "session_id": "uuid",
  "include_document_findings": true
}
```

---

### Wellbeing Chat (Placeholder)

```
POST /api/wellbeing/chat
```

Returns a placeholder — wellbeing module is not yet implemented.

---

## Example curl Requests

```bash
# Health check
curl http://localhost:8000/health

# Diagnosis chat
curl -X POST http://localhost:8000/api/diagnosis/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I have been having chest tightness and shortness of breath"}'

# Explain a medical term
curl -X POST http://localhost:8000/api/medical/explain-term \
  -H "Content-Type: application/json" \
  -d '{"term": "tachycardia"}'

# Upload a document
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@/path/to/labresult.pdf"
```

---

## Running Tests

```bash
pytest app/tests/ -v
```

Tests cover:
- Diagnosis chat schema validation
- Wellbeing placeholder response
- Emergency red flag detection
- Urgency classification
- Document parser text extraction
- Safety guardrails

---

## Safety Limitations

- Vital AI **cannot diagnose** medical conditions.
- Vital AI **cannot prescribe** medications or give dosing instructions.
- Vital AI **cannot replace** professional medical care.
- All responses include a medical disclaimer.
- Emergency symptoms trigger an immediate escalation to seek emergency care.
- Likelihood categories (`more_likely`, `possible`, `less_likely`, `cannot_rule_out`) are AI-estimated and must not be treated as diagnosis.

**If you or someone you know is experiencing a medical emergency, call 911 (US) or your local emergency number immediately.**

---

## Future Frontend Integration

The backend exposes a RESTful JSON API. The frontend (to be built separately) should:
- Call `POST /api/diagnosis/chat` for the main chat interface
- Persist `session_id` across turns for conversation continuity
- Display `urgency.level` prominently (red banner for emergency)
- Show `nearest_care_suggestions` on a map when available
- Render `doctor_visit_document` as a printable/shareable card

---

## Future Improvements

- [ ] Real authentication (JWT / OAuth2)
- [ ] Real vector search with ChromaDB/FAISS + trusted source ingestion
- [ ] Google Maps Places API integration for real provider search
- [ ] Wellbeing / mental health chat module
- [ ] Session history and multi-turn context injection
- [ ] Image-based symptom analysis (wound photos, rashes)
- [ ] Multi-language support
- [ ] HIPAA compliance review before production deployment
- [ ] Rate limiting and abuse prevention
- [ ] Alembic migration scripts
