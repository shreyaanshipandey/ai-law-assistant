"""
AI Law Assistant — FastAPI application entrypoint.

Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, auth, bns_kb, case_management, cases, chatbot, helplines, petitions
from app.core.config import settings
from app.db.database import init_db
from app.services.rag_service import bootstrap_default_kb

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    bootstrap_default_kb()
    yield
    # Shutdown (nothing to clean up currently)


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered legal assistant for Indian law, grounded in the Bharatiya Nyaya Sanhita (BNS).",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)
app.include_router(cases.router, prefix=settings.API_V1_PREFIX)
app.include_router(petitions.router, prefix=settings.API_V1_PREFIX)
app.include_router(chatbot.router, prefix=settings.API_V1_PREFIX)
app.include_router(bns_kb.router, prefix=settings.API_V1_PREFIX)
app.include_router(helplines.router, prefix=settings.API_V1_PREFIX)
app.include_router(case_management.router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": settings.APP_NAME, "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}
