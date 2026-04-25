Build the BACKEND ONLY for an Agentic AI healthcare assistant app called Vital AI

Do not build any frontend. The frontend will be integrated later.

The app has two chat modes:

1. Diagnosis / Medical Navigation Chat
2. Wellbeing Chat

For now, fully implement only the Diagnosis / Medical Navigation Chat backend.

For the Wellbeing Chat:
- Create only placeholder routes and structure.
- Do not write a psychiatrist/therapy/wellbeing system prompt yet.
- Return a placeholder response saying the wellbeing module is not configured yet.

Use a SKILL-BASED AGENT ARCHITECTURE.

Do NOT create a separate autonomous agent for every feature.

Instead, create one main DiagnosisChatAgent that loads and calls different skills depending on the user's problem.

Architecture idea:

DiagnosisChatAgent
  ├── MedicalDocumentSkill
  ├── MedicalJargonSkill
  ├── SymptomConsultationSkill
  ├── UrgencyClassificationSkill
  ├── PossibleCausesSkill
  ├── TemporaryMitigationSkill
  ├── ProviderTypeSkill
  ├── CareLocatorSkill
  └── DoctorVisitPrepSkill

The DiagnosisChatAgent should:
- Receive the user message and context
- Detect user intent
- Decide which skills are needed
- Call the relevant skills
- Combine the skill outputs
- Run medical safety guardrails
- Return a structured JSON response

Important healthcare safety rules:
- The app must NOT claim to diagnose the user.
- Avoid saying: “You have X disease.”
- Prefer: “This could be associated with…”, “Possible causes include…”, or “A clinician can evaluate…”
- Do not give definitive disease probabilities.
- If possible conditions are shown, use likelihood categories:
  - more_likely
  - possible
  - less_likely
  - cannot_rule_out
- If the user asks for probabilities, return only rough AI-estimated likelihood ranges with strong disclaimers.
- Do not recommend stopping medication.
- Do not give prescription medication instructions.
- Do not provide dangerous medication dosing.
- Always include a medical disclaimer.
- Emergency or red-flag symptoms must override normal responses.

Use Python + FastAPI.

Tech stack:
- Python
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite by default for local development
- Alembic migrations
- python-dotenv
- OpenAI API or a generic LLM provider wrapper
- ChromaDB or FAISS for vector search abstraction
- pypdf or pdfplumber for PDF parsing
- pytesseract or OCR abstraction for image documents
- pytest for testing

Create this project structure:

carecompass-backend/
  app/
    main.py
    config.py

    api/
      routes/
        diagnosis_chat.py
        wellbeing_chat.py
        documents.py
        medical.py
        doctor_visit.py
        health.py

    agents/
      diagnosis_agent.py
      wellbeing_agent.py

    skills/
      medical_document_skill.py
      medical_jargon_skill.py
      symptom_consultation_skill.py
      urgency_classification_skill.py
      possible_causes_skill.py
      temporary_mitigation_skill.py
      provider_type_skill.py
      care_locator_skill.py
      doctor_visit_prep_skill.py

    safety/
      medical_safety_guardrails.py

    services/
      llm_service.py
      rag_service.py
      document_parser.py
      location_service.py
      doctor_document_generator.py

    models/
      database.py
      user.py
      chat.py
      document.py
      doctor_visit.py

    schemas/
      chat.py
      document.py
      urgency.py
      doctor_visit.py
      common.py

    prompts/
      diagnosis_system_prompt.py
      medical_document_prompt.py
      medical_jargon_prompt.py
      symptom_consultation_prompt.py
      urgency_prompt.py
      possible_causes_prompt.py
      temporary_mitigation_prompt.py
      provider_type_prompt.py
      doctor_visit_prompt.py
      safety_prompt.py

    data/
      trusted_sources_seed.json

    tests/
      test_diagnosis_chat.py
      test_wellbeing_placeholder.py
      test_urgency_classification.py
      test_safety_guardrails.py
      test_document_parser.py

  requirements.txt
  .env.example
  README.md

Core API Endpoints:

1. Diagnosis Chat Endpoint

POST /api/diagnosis/chat

Request body:

{
  "user_id": "string optional",
  "session_id": "string optional",
  "message": "string",
  "location": {
    "latitude": "number optional",
    "longitude": "number optional",
    "city": "string optional",
    "state": "string optional",
    "country": "string optional"
  },
  "user_context": {
    "age": "number optional",
    "sex": "string optional",
    "pregnant": "boolean optional",
    "known_conditions": ["string"],
    "medications": ["string"],
    "allergies": ["string"]
  }
}

Response body:

{
  "response": "string",
  "intent": "symptoms | document_explanation | jargon_explanation | doctor_visit_prep | care_navigation | general_health | unknown",
  "urgency": {
    "level": "emergency | urgent | soon | routine | self_care | unknown",
    "reason": "string",
    "red_flags": ["string"],
    "recommended_timeframe": "string"
  },
  "possible_causes": [
    {
      "name": "string",
      "likelihood": "more_likely | possible | less_likely | cannot_rule_out",
      "reasoning": "string",
      "disclaimer": "string"
    }
  ],
  "temporary_mitigation": [
    {
      "title": "string",
      "description": "string",
      "safety_note": "string"
    }
  ],
  "recommended_provider_type": {
    "specialty": "ER | urgent_care | primary_care | pediatrician | ophthalmologist | orthopedist | gynecologist | dermatologist | cardiologist | neurologist | gastroenterologist | ENT | dentist | psychiatrist | therapist | other | unknown",
    "reason": "string"
  },
  "doctor_visit_document": {
    "summary": "string",
    "concerns": ["string"],
    "symptom_timeline": ["string"],
    "questions_to_ask": ["string"],
    "important_details_to_share": ["string"]
  },
  "nearest_care_suggestions": [
    {
      "name": "string",
      "type": "string",
      "address": "string",
      "distance": "string optional",
      "phone": "string optional",
      "source": "string optional"
    }
  ],
  "safety_disclaimer": "string"
}

2. Medical Document Upload Endpoint

POST /api/documents/upload

Accept:
- PDF files
- image files
- text files

Backend behavior:
- Extract text from the document
- Store document metadata
- Store extracted text
- Return a preview of extracted text
- Allow the document to be linked to a diagnosis chat session later

Response body:

{
  "document_id": "string",
  "filename": "string",
  "extracted_text_preview": "string",
  "status": "processed | failed"
}

3. Medical Document Explanation Endpoint

POST /api/documents/explain

Request body:

{
  "document_id": "string optional",
  "raw_text": "string optional",
  "user_context": {
    "age": "number optional",
    "sex": "string optional",
    "known_conditions": ["string"],
    "medications": ["string"],
    "allergies": ["string"]
  }
}

Response body:

{
  "plain_language_summary": "string",
  "key_findings": [
    {
      "finding": "string",
      "simple_explanation": "string",
      "normal_or_abnormal": "normal | high | low | unclear | not_applicable",
      "why_it_matters": "string"
    }
  ],
  "medical_terms": [
    {
      "term": "string",
      "meaning": "string"
    }
  ],
  "questions_for_doctor": ["string"],
  "urgency_flags": ["string"],
  "disclaimer": "string"
}

4. Medical Jargon Explanation Endpoint

POST /api/medical/explain-term

Request body:

{
  "term": "string",
  "context": "string optional"
}

Response body:

{
  "term": "string",
  "simple_explanation": "string",
  "deeper_explanation": "string",
  "example": "string",
  "when_to_ask_a_doctor": "string"
}

5. Doctor Visit Preparation Endpoint

POST /api/doctor-visit/prepare

Request body:

{
  "session_id": "string",
  "include_document_findings": true
}

Response body:

{
  "visit_summary_markdown": "string",
  "concerns": ["string"],
  "symptom_timeline": ["string"],
  "questions_to_ask": ["string"],
  "medications_to_mention": ["string"],
  "red_flags_to_watch": ["string"],
  "recommended_provider_type": {
    "specialty": "string",
    "reason": "string"
  }
}

6. Wellbeing Chat Placeholder Endpoint

POST /api/wellbeing/chat

For now:
- Do not implement wellbeing logic.
- Do not add a psychiatrist or therapy system prompt.
- Return a placeholder response.

Response body:

{
  "response": "Wellbeing chat module is not configured yet.",
  "status": "placeholder"
}

DiagnosisChatAgent behavior:

The DiagnosisChatAgent should perform this flow:

1. Receive user message and context.
2. Identify intent:
   - symptoms
   - medical document explanation
   - medical jargon explanation
   - doctor visit preparation
   - care navigation
   - general health question
   - unknown
3. Load only the required skills.
4. Call the relevant skills.
5. Run safety guardrails.
6. Combine outputs into the final response.
7. Return structured JSON.

Required skills:

1. MedicalDocumentSkill

Purpose:
- Explain medical documents in simple language.

Capabilities:
- Summarize medical document text.
- Extract key findings.
- Explain abnormal or unclear values.
- Extract medical jargon.
- Generate questions for doctor.
- Detect urgency flags in document text.

2. MedicalJargonSkill

Purpose:
- Explain medical terms.

Capabilities:
- Give simple explanation.
- Give deeper explanation.
- Provide example.
- Explain when user should ask a doctor.

3. SymptomConsultationSkill

Purpose:
- Handle symptom-related chat.

Capabilities:
- Ask relevant follow-up questions.
- Extract symptoms.
- Extract onset, duration, severity, location, triggers, and associated symptoms.
- Use user context such as age, sex, pregnancy, medications, allergies, and known conditions.

4. UrgencyClassificationSkill

Purpose:
- Classify medical urgency.

Urgency levels:
- emergency
- urgent
- soon
- routine
- self_care
- unknown

Must detect red flags including:
- chest pain
- trouble breathing
- stroke-like symptoms
- severe allergic reaction
- severe bleeding
- overdose
- suicidal or self-harm language
- severe abdominal pain
- pregnancy danger signs
- sudden vision loss
- head injury with confusion
- fainting
- seizure
- severe dehydration
- high fever in infants
- severe pain after injury

5. PossibleCausesSkill

Purpose:
- Suggest possible causes without diagnosing.

Output likelihood categories:
- more_likely
- possible
- less_likely
- cannot_rule_out

Do not output definitive diagnoses.

6. TemporaryMitigationSkill

Purpose:
- Suggest safe temporary steps while waiting for care.

Allowed examples:
- rest
- hydration
- avoiding triggers
- monitoring symptoms
- applying ice or heat for minor injuries
- avoiding contact lenses for eye irritation
- seeking care if symptoms worsen

Not allowed:
- prescription medication advice
- stopping medications
- dangerous dosage instructions
- replacing professional care

7. ProviderTypeSkill

Purpose:
- Suggest which type of healthcare provider to visit.

Supported provider types:
- ER
- urgent care
- primary care physician
- pediatrician
- ophthalmologist
- orthopedist
- gynecologist
- dermatologist
- cardiologist
- neurologist
- gastroenterologist
- ENT
- dentist
- psychiatrist
- therapist
- other

Examples:
- Sudden vision loss -> ER or ophthalmologist depending urgency
- Broken bone suspicion -> urgent care, ER, or orthopedist
- Pregnancy danger signs -> ER or gynecologist/OB-GYN
- Child high fever -> pediatrician or ER depending severity
- Chest pain with shortness of breath -> ER
- Tooth pain -> dentist
- Skin rash -> primary care or dermatologist

8. CareLocatorSkill

Purpose:
- Suggest nearest care options.

For now:
- Implement a mock location_service.py.
- If location is provided, return mock nearby providers based on provider type.
- Structure code so Google Maps API or another real provider search API can be added later.

9. DoctorVisitPrepSkill

Purpose:
- Generate a doctor-facing visit summary.

Should include:
- main concerns
- symptom timeline
- important details
- document findings if available
- medications
- allergies
- questions to ask
- red flags to mention
- recommended provider type

Medical safety guardrails:

Create app/safety/medical_safety_guardrails.py.

Safety guardrails must:
- Inspect user message
- Inspect skill outputs
- Detect emergency red flags
- Override response if emergency is detected
- Prevent diagnosis claims
- Prevent unsafe medication advice
- Ensure disclaimer is included

If emergency red flags are detected, final response must prioritize:

"Based on what you described, this may be urgent. Please seek emergency medical care now or call your local emergency number. I cannot diagnose you, but these symptoms can be serious."

Then include only brief next steps.

Prompts:

Create separate prompt files:

1. diagnosis_system_prompt.py

Should define the main DiagnosisChatAgent behavior:
- You are a medical navigation assistant.
- You are not a doctor.
- You do not diagnose.
- You provide educational support, urgency guidance, and doctor-visit preparation.
- Use simple language.
- Ask clarifying questions when necessary.
- Use structured JSON output.
- Always include safety disclaimers.
- Escalate emergencies.

2. medical_document_prompt.py

Should instruct the model to:
- Explain documents in plain English.
- Extract key findings.
- Explain terms.
- Identify unclear or abnormal values.
- Generate doctor questions.
- Avoid diagnosis.

3. symptom_consultation_prompt.py

Should instruct the model to:
- Ask follow-up questions.
- Extract symptom details.
- Avoid diagnosis.
- Prepare data for urgency and possible causes skills.

4. urgency_prompt.py

Should instruct the model to:
- Classify urgency.
- Identify red flags.
- Recommend timeframe.
- Prioritize emergency guidance when needed.

5. possible_causes_prompt.py

Should instruct the model to:
- Suggest possible causes using likelihood categories.
- Never provide definitive diagnosis.
- Explain reasoning briefly.

6. temporary_mitigation_prompt.py

Should instruct the model to:
- Suggest safe temporary steps.
- Avoid risky medical instructions.
- Include warning signs.

7. provider_type_prompt.py

Should instruct the model to:
- Recommend suitable provider type.
- Explain why.
- Escalate to ER when symptoms suggest emergency.

8. doctor_visit_prompt.py

Should instruct the model to:
- Generate a concise doctor-facing summary.
- Include symptom timeline.
- Include questions to ask.
- Include important medical context.

9. safety_prompt.py

Should instruct the model to:
- Detect unsafe content.
- Detect red flags.
- Override unsafe responses.
- Keep language cautious and safe.

Database models:

Create SQLAlchemy models for:

1. User
- id
- created_at

2. ChatSession
- id
- user_id
- mode
- created_at
- updated_at

3. ChatMessage
- id
- session_id
- role
- content
- created_at

4. UploadedDocument
- id
- user_id
- session_id
- filename
- file_type
- extracted_text
- created_at

5. DoctorVisitSummary
- id
- session_id
- summary_markdown
- created_at

Use SQLite by default.

Make DATABASE_URL configurable through environment variables.

RAG / trusted source abstraction:

Create rag_service.py.

Do not scrape websites now.

Create data/trusted_sources_seed.json with placeholder metadata for:
- MedlinePlus
- CDC
- WHO
- NIH
- NHS
- SAMHSA

rag_service.py should expose:
- search_trusted_sources(query: str) -> list
- get_context_for_query(query: str) -> str

For now, it can return placeholder trusted source snippets.

Environment variables:

Create .env.example:

OPENAI_API_KEY=
DATABASE_URL=sqlite:///./carecompass.db
LLM_MODEL=gpt-4.1-mini
VECTOR_DB_PATH=./vector_db
GOOGLE_MAPS_API_KEY=

Testing requirements:

Use pytest.

Create tests for:
- diagnosis chat route returns valid schema
- wellbeing route returns placeholder
- emergency red flag detection works
- urgency classification works
- document parser extracts text from simple text file
- provider type classifier returns expected specialty
- doctor visit prep generates markdown

README requirements:

Write a README with:
- project overview
- architecture explanation
- setup instructions
- environment variables
- how to run the FastAPI server
- API endpoint documentation
- example curl requests
- safety limitations
- future frontend integration notes
- future improvements

Implementation quality:
- Use type hints.
- Use Pydantic schemas for all request and response bodies.
- Use modular code.
- Add docstrings where helpful.
- Add TODO comments for future integrations.
- Make the backend runnable locally with:

uvicorn app.main:app --reload

Do not create frontend files.
Do not implement real payment logic.
Do not implement real user authentication yet.
Do not implement real maps API yet.
Do not implement wellbeing chat logic yet.
Only create the backend structure and working diagnosis chat flow with skills.