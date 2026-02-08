# main.py
"""
Aplicação FastAPI para predição de desempenho de estudantes
"""
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import (
    logger, 
    STATIC_DIR, 
    INDEX_HTML, 
    ALLOWED_ORIGINS
)
from app.services.model_service import ModelService
from app.services.student_service import StudentService
from app.services.prediction_service import PredictionService
from app.routes import health, students, predictions


# ---------- App ----------
app = FastAPI(title="Student Performance API")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar arquivos estáticos
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    logger.info(f"Mounted static: {STATIC_DIR}")
else:
    logger.info(f"Static dir not found: {STATIC_DIR}")


# ---------- Startup ----------
@app.on_event("startup")
def startup_event():
    """
    Inicializa serviços ao iniciar a aplicação
    """
    # Inicializar serviço de modelo
    model_service = ModelService()
    model_service.initialize()
    app.state.model_service = model_service
    
    # Inicializar serviço de estudantes
    student_service = StudentService(model_service)
    app.state.student_service = student_service
    
    # Inicializar serviço de predição
    prediction_service = PredictionService(model_service)
    app.state.prediction_service = prediction_service
    
    logger.info("All services initialized successfully")


# ---------- Routes ----------
@app.get("/", response_class=HTMLResponse)
def serve_index():
    """
    Serve a página HTML principal
    """
    if INDEX_HTML.exists():
        return FileResponse(str(INDEX_HTML))
    return HTMLResponse(
        "<html><body>"
        "<h3>Student Performance API</h3>"
        f"<p>Arquivo index.html não encontrado em {INDEX_HTML}</p>"
        "</body></html>"
    )


# Registrar routers
app.include_router(health.router, tags=["Health"])
app.include_router(students.router, tags=["Students"])
app.include_router(predictions.router, tags=["Predictions"])
