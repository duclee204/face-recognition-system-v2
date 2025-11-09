"""
System API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from loguru import logger

from app.core.database import get_db
from app.models.schemas import (
    SystemStatusResponse, TrainModelRequest, TrainModelResponse
)
from app.services.face_recognition import face_service
from app.services.employee import employee_service
from app.services.camera import camera_service

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    db: Session = Depends(get_db)
):
    """
    Get system status
    
    Returns:
    - Total employees
    - Model loaded status
    - InsightFace loaded status
    - Camera availability
    - Last training time (if available)
    """
    try:
        # Count employees
        total_employees = employee_service.count_employees(db, is_active=True)
        
        # Check model status
        model_loaded = face_service.model_loaded and face_service.svm_model is not None
        insightface_loaded = face_service.app is not None
        
        # Check camera
        camera_available = False
        try:
            if camera_service.open_camera():
                camera_available = True
                camera_service.close_camera()
        except:
            pass
        
        return SystemStatusResponse(
            status="operational" if insightface_loaded else "degraded",
            total_employees=total_employees,
            model_loaded=model_loaded,
            insightface_loaded=insightface_loaded,
            camera_available=camera_available,
            last_trained=None  # TODO: Store training timestamp
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/train-model", response_model=TrainModelResponse)
async def train_model(
    request: TrainModelRequest,
    db: Session = Depends(get_db)
):
    """
    Train SVM classifier model
    
    This should be called:
    - After adding new employees
    - Periodically to improve accuracy
    - When force_retrain is True
    """
    try:
        # Load employee database from MySQL
        employee_service.rebuild_face_db(db)
        
        # Check if we have employees
        if len(face_service.employee_db) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No employees in database to train on"
            )
        
        # Check if retraining is needed
        if not request.force_retrain and face_service.model_loaded:
            return TrainModelResponse(
                success=True,
                message="Model already trained. Use force_retrain=true to retrain."
            )
        
        # Train model
        logger.info("Starting model training...")
        training_stats = face_service.train_svm_classifier()
        
        return TrainModelResponse(
            success=True,
            message=f"Model trained successfully on {training_stats['num_employees']} employees",
            training_time=training_stats['training_time'],
            model_accuracy=training_stats['accuracy'],
            total_samples=training_stats['total_samples']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error training model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/reload-models")
async def reload_models(
    db: Session = Depends(get_db)
):
    """
    Reload all models and databases
    
    Useful after:
    - Database changes
    - Manual file updates
    - System restart
    """
    try:
        # Reload employee database
        employee_service.rebuild_face_db(db)
        
        # Reload SVM model
        face_service.load_svm_model()
        
        return {
            "success": True,
            "message": "Models reloaded successfully",
            "employees_loaded": len(face_service.employee_db),
            "model_loaded": face_service.model_loaded
        }
        
    except Exception as e:
        logger.error(f"Error reloading models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/info")
async def get_system_info(
    db: Session = Depends(get_db)
):
    """
    Get detailed system information
    """
    try:
        total_employees = employee_service.count_employees(db, is_active=True)
        
        return {
            "success": True,
            "info": {
                "version": "1.0.0",
                "total_employees": total_employees,
                "insightface_loaded": face_service.app is not None,
                "model_loaded": face_service.model_loaded,
                "employee_db_size": len(face_service.employee_db),
                "recognition_threshold": face_service.app.det_thresh if face_service.app else None,
                "storage_paths": {
                    "employee_images": str(face_service.app.root) if face_service.app else None,
                    "models": "app/storage/models"
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
