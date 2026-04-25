from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.models.database import create_tables
from app.api.routes import health, diagnosis_chat, wellbeing_chat, documents, medical, doctor_visit

BASE_DIR = Path(__file__).parent.parent

app = FastAPI(
    title="Vital AI Backend",
    description="Agentic AI healthcare navigation assistant backend.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict to frontend origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.on_event("startup")
async def startup():
    create_tables()


@app.get("/", include_in_schema=False)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


app.include_router(health.router, tags=["Health"])
app.include_router(diagnosis_chat.router, prefix="/api/diagnosis", tags=["Diagnosis Chat"])
app.include_router(wellbeing_chat.router, prefix="/api/wellbeing", tags=["Wellbeing Chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(medical.router, prefix="/api/medical", tags=["Medical"])
app.include_router(doctor_visit.router, prefix="/api/doctor-visit", tags=["Doctor Visit"])
