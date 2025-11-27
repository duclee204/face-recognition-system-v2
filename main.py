"""
Main FastAPI application
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
import sys
import os

from app.core.config import settings
from app.core.database import init_db
from app.api import recognition, auto_registration, employees, head_pose
from app.services.face_recognition import face_service

# Configure loguru
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level="DEBUG"
)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Face Recognition Attendance System with FastAPI",
    version="1.0.0",
    debug=settings.DEBUG
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("🚀 Starting Face Recognition System...")
    
    try:
        # Initialize database
        init_db()
        logger.info("✅ Database initialized")
        
        # Load face recognition models
        face_service.load_employee_db()
        face_service.load_svm_model()
        logger.info("✅ Face recognition models loaded")
        
        logger.info(f"🎉 System ready! Running on {settings.HOST}:{settings.PORT}")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down Face Recognition System...")
    # Add cleanup tasks here if needed


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - serve main page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/registration", response_class=HTMLResponse)
async def registration_page(request: Request):
    """Registration page"""
    return templates.TemplateResponse("registration.html", {"request": request})


@app.get("/recognition", response_class=HTMLResponse)
async def recognition_page(request: Request):
    """Recognition page"""
    return templates.TemplateResponse("recognition.html", {"request": request})


@app.get("/employees", response_class=HTMLResponse)
async def employees_page(request: Request):
    """Employee list page"""
    return templates.TemplateResponse("employees.html", {"request": request})


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "face-recognition-api"
    }


# Include routers
app.include_router(employees.router, prefix=settings.API_V1_PREFIX)
app.include_router(auto_registration.router, prefix=settings.API_V1_PREFIX)
app.include_router(recognition.router, prefix=settings.API_V1_PREFIX)
app.include_router(head_pose.router, prefix=settings.API_V1_PREFIX)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
