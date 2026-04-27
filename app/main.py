from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import properties, calls, export
from app.database import init_db

app = FastAPI(
    title="AI Phone Automation",
    description="AI電話外呼システム — 房地产空房确认",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(properties.router)
app.include_router(calls.router)
app.include_router(export.router)


@app.get("/")
def health():
    return {"status": "running", "version": "1.0.0"}
