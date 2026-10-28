"""
backend/app/main.py - Main FastAPI Application Entrypoint
SmartTriage AI - Talent AP Mega Hackathon 2026
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.api.routes import router as api_router

app = FastAPI(
    title="SmartTriage AI - OPD Clinical Decision Support",
    description="OPD Triage Assistant for High-Volume Government Hospitals (Talent AP H1)",
    version="2.0.0"
)

# Enable CORS for React frontend (Vite dev server default ports 5173/3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)

# Mount frontend build or static directory
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
frontend_static = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")

if os.path.exists(frontend_dist) and os.path.exists(os.path.join(frontend_dist, "index.html")):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_react_app(full_path: str):
        if full_path.startswith("api"):
            return None
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
elif os.path.exists(os.path.join(frontend_static, "index.html")):
    app.mount("/static", StaticFiles(directory=frontend_static), name="static")

    @app.get("/")
    def serve_static_app():
        return FileResponse(os.path.join(frontend_static, "index.html"))
