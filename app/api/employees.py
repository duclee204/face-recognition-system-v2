"""
Employee API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import cv2
import numpy as np
import base64
import os
import json
from datetime import datetime
from loguru import logger

from app.core.database import get_db
from app.models.schemas import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeListResponse,
    RegistrationStartRequest, RegistrationFrameData, RegistrationCompleteRequest,
    RegistrationResponse
)
from app.services.employee import employee_service
from app.services.face_recognition import face_service
from app.core.config import settings

router = APIRouter(prefix="/employees", tags=["employees"])

# Temporary storage for registration sessions
registration_sessions = {}


@router.post("/register/upload", response_model=RegistrationResponse)
async def register_with_images(
    employee_code: str = Form(...),
    name: str = Form(..., description="Employee full name"),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    position: Optional[str] = Form(None),
    images: List[UploadFile] = File(..., description="Upload 5-20 face images"),
    db: Session = Depends(get_db)
):
    """
    Register employee by uploading multiple images
    
    Client uploads 5-20 images of the employee's face from different angles
    System will extract embeddings and train the model
    """
    try:
        start_time = datetime.now()
        
        # Validate number of images
        if len(images) < 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Need at least 5 images. Provided: {len(images)}"
            )
        
        if len(images) > 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum 30 images allowed. Provided: {len(images)}"
            )
        
        # Check if employee code already exists
        existing = employee_service.get_employee_by_code(db, employee_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Employee code '{employee_code}' already exists"
            )
        
        logger.info(f"📸 Processing {len(images)} uploaded images for {employee_code}")
        
        # Read and decode images
        frames = []
        for idx, image_file in enumerate(images):
            try:
                # Read image file
                image_data = await image_file.read()
                nparr = np.frombuffer(image_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is None:
                    logger.warning(f"⚠️ Image {idx+1} could not be decoded, skipping...")
                    continue
                
                frames.append(frame)
                
            except Exception as e:
                logger.warning(f"⚠️ Error reading image {idx+1}: {e}")
                continue
        
        if len(frames) < 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {len(frames)} valid images found. Need at least 5."
            )
        
        # Extract embeddings from frames
        logger.info(f"🔍 Extracting face embeddings from {len(frames)} images...")
        embeddings, successful_frames = face_service.process_registration_frames(frames)
        
        if len(embeddings) < 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only detected {len(embeddings)} valid faces. Need at least 5. Make sure faces are clear and visible."
            )
        
        # Save embeddings
        embeddings_array, mean_embedding = face_service.save_employee_embeddings(
            employee_code,
            embeddings
        )
        
        # Save sample images
        employee_img_dir = os.path.join(settings.EMPLOYEE_IMAGES_PATH, employee_code)
        os.makedirs(employee_img_dir, exist_ok=True)
        
        saved_image_paths = []
        for idx, frame in enumerate(frames[:10]):  # Save first 10 images as samples
            img_path = os.path.join(employee_img_dir, f"sample_{idx}.jpg")
            cv2.imwrite(img_path, frame)
            saved_image_paths.append(img_path)
        
        # Create employee data (map 'name' to 'full_name')
        employee_data = EmployeeCreate(
            employee_code=employee_code,
            full_name=name,  # Map form field 'name' to schema field 'full_name'
            email=email,
            phone=phone,
            department=department,
            position=position
        )
        
        # Save to database
        db_employee = employee_service.create_employee(
            db=db,
            employee_data=employee_data,
            embeddings=embeddings_array.tolist(),
            mean_embedding=mean_embedding.tolist(),
            image_paths=saved_image_paths
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Registration completed: {employee_code} - {processing_time:.2f}s")
        
        # Auto-train SVM model after successful registration
        total_employees = employee_service.count_employees(db)
        if total_employees >= 2:
            logger.info(f"🔄 Auto-training SVM model with {total_employees} employees...")
            try:
                train_result = face_service.train_svm_classifier()
                logger.info(f"✅ SVM model trained: {train_result['num_employees']} employees, "
                           f"accuracy: {train_result['accuracy']:.3f}, time: {train_result['training_time']:.2f}s")
            except Exception as train_error:
                logger.warning(f"⚠️ SVM training failed: {train_error}")
        else:
            logger.info(f"ℹ️ Only {total_employees} employee(s). Need at least 2 to train SVM model.")
        
        return RegistrationResponse(
            success=True,
            message=f"Registration completed successfully. {len(embeddings)} embeddings created from {len(frames)} images.",
            employee_id=db_employee.id,
            total_embeddings=len(embeddings),
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in upload registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/register/start", response_model=RegistrationResponse)
async def start_registration(
    request: RegistrationStartRequest,
    db: Session = Depends(get_db)
):
    """
    Start employee registration process
    
    Creates a registration session for circular face scanning
    """
    try:
        # Check if employee code already exists
        existing = employee_service.get_employee_by_code(db, request.employee_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Employee code {request.employee_code} already exists"
            )
        
        # Create session ID
        session_id = f"{request.employee_code}_{int(datetime.now().timestamp())}"
        
        # Initialize session
        registration_sessions[session_id] = {
            "employee_data": request.model_dump(),
            "frames": [],
            "start_time": datetime.now(),
            "status": "recording"
        }
        
        logger.info(f"Started registration session: {session_id}")
        
        return RegistrationResponse(
            success=True,
            message="Registration session started. Please scan face in circular motion.",
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/register/frame/{session_id}")
async def upload_registration_frame(
    session_id: str,
    frame_data: RegistrationFrameData
):
    """
    Upload a frame during registration (circular scanning)
    
    Client should send frames continuously while user rotates face
    """
    try:
        if session_id not in registration_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration session not found"
            )
        
        session = registration_sessions[session_id]
        
        if session["status"] != "recording":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is not in recording state"
            )
        
        # Decode base64 image
        img_data = base64.b64decode(frame_data.frame_data.split(',')[1] if ',' in frame_data.frame_data else frame_data.frame_data)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image data"
            )
        
        # Add frame to session
        session["frames"].append(frame)
        
        # Auto-select best frames (every 5th frame to avoid too similar frames)
        if len(session["frames"]) % 5 == 0:
            logger.info(f"Session {session_id}: {len(session['frames'])} frames collected")
        
        return {
            "success": True,
            "frames_collected": len(session["frames"]),
            "message": "Frame received"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading frame: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/register/complete", response_model=RegistrationResponse)
async def complete_registration(
    request: RegistrationCompleteRequest,
    db: Session = Depends(get_db)
):
    """
    Complete registration and process all frames
    
    This will:
    1. Process all collected frames
    2. Extract face embeddings
    3. Create augmented samples
    4. Save to database
    5. Trigger model retraining
    """
    try:
        if request.session_id not in registration_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration session not found"
            )
        
        session = registration_sessions[request.session_id]
        session["status"] = "processing"
        
        employee_data = EmployeeCreate(**session["employee_data"])
        frames = session["frames"]
        
        if len(frames) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough frames. Collected: {len(frames)}, Required: at least 10"
            )
        
        start_time = datetime.now()
        
        # Process frames to extract embeddings
        logger.info(f"Processing {len(frames)} frames for {employee_data.employee_code}")
        embeddings, successful_frames = face_service.process_registration_frames(frames)
        
        if len(embeddings) < 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough valid face embeddings. Got: {len(embeddings)}, Required: at least 5"
            )
        
        # Save embeddings
        embeddings_array, mean_embedding = face_service.save_employee_embeddings(
            employee_data.employee_code,
            embeddings
        )
        
        # Save sample images
        employee_img_dir = os.path.join(settings.EMPLOYEE_IMAGES_PATH, employee_data.employee_code)
        os.makedirs(employee_img_dir, exist_ok=True)
        
        saved_image_paths = []
        # Save every 10th frame as sample
        for idx in range(0, len(frames), 10):
            img_path = os.path.join(employee_img_dir, f"sample_{idx}.jpg")
            cv2.imwrite(img_path, frames[idx])
            saved_image_paths.append(img_path)
        
        # Create employee in database
        db_employee = employee_service.create_employee(
            db=db,
            employee_data=employee_data,
            embeddings=embeddings_array.tolist(),
            mean_embedding=mean_embedding.tolist(),
            image_paths=saved_image_paths
        )
        
        # Clean up session
        del registration_sessions[request.session_id]
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Registration completed: {employee_data.employee_code} - {processing_time:.2f}s")
        
        # Auto-train SVM model after successful registration
        total_employees = employee_service.count_employees(db)
        if total_employees >= 2:
            logger.info(f"🔄 Auto-training SVM model with {total_employees} employees...")
            try:
                train_result = face_service.train_svm_classifier()
                logger.info(f"✅ SVM model trained: {train_result['num_employees']} employees, "
                           f"accuracy: {train_result['accuracy']:.3f}, time: {train_result['training_time']:.2f}s")
            except Exception as train_error:
                logger.warning(f"⚠️ SVM training failed: {train_error}")
        else:
            logger.info(f"ℹ️ Only {total_employees} employee(s). Need at least 2 to train SVM model.")
        
        return RegistrationResponse(
            success=True,
            message=f"Registration completed successfully. {len(embeddings)} embeddings created.",
            employee_id=db_employee.id,
            total_embeddings=len(embeddings),
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/", response_model=EmployeeListResponse)
async def get_employees(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get list of employees"""
    employees = employee_service.get_employees(db, skip, limit, is_active)
    total = employee_service.count_employees(db, is_active)
    
    return EmployeeListResponse(
        total=total,
        employees=employees
    )


@router.post("/", response_model=EmployeeResponse)
async def create_employee(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new employee (without face data)
    Face data will be registered later via /api/auto-registration/register-face
    """
    try:
        # Check if employee_code already exists
        existing = employee_service.get_employee_by_code(db, employee_data.employee_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Employee code {employee_data.employee_code} already exists"
            )
        
        # Create employee without embeddings
        db_employee = employee_service.create_employee(
            db=db,
            employee_data=employee_data,
            embeddings=[],
            mean_embedding=[],
            image_paths=[]
        )
        
        logger.info(f"✅ Employee created: {employee_data.employee_code} - {employee_data.full_name}")
        
        return db_employee
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating employee: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """Get employee by ID"""
    employee = employee_service.get_employee(db, employee_id)
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    return employee


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    employee_update: EmployeeUpdate,
    db: Session = Depends(get_db)
):
    """Update employee information"""
    employee = employee_service.update_employee(db, employee_id, employee_update)
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    return employee


@router.post("/{employee_code}/train")
async def train_model(
    employee_code: str,
    db: Session = Depends(get_db)
):
    """Train SVM classifier model with all employee embeddings"""
    try:
        # Verify employee exists
        employee = employee_service.get_employee_by_code(db, employee_code)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with code {employee_code} not found"
            )
        
        # Check if employee has face embeddings
        if not employee.face_embeddings or len(employee.face_embeddings) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee has no face embeddings. Please capture faces first."
            )
        
        # Reload employee database to face service
        face_service.load_employee_db()
        
        # Train SVM model
        total_employees = employee_service.count_employees(db, status='active')
        if total_employees < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Need at least 2 employees to train model. Current: {total_employees}"
            )
        
        logger.info(f"🔄 Training SVM model with {total_employees} active employees...")
        train_result = face_service.train_svm_classifier()
        
        logger.info(f"✅ SVM model trained: {train_result['num_employees']} employees, "
                   f"accuracy: {train_result['accuracy']:.3f}, "
                   f"time: {train_result['training_time']:.2f}s")
        
        return {
            "success": True,
            "message": "Model trained successfully",
            "stats": train_result
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error training model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to train model: {str(e)}"
        )


@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """Delete employee (soft delete) and retrain model"""
    success = employee_service.delete_employee(db, employee_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Auto-retrain SVM model after deletion
    total_employees = employee_service.count_employees(db, status='active')
    if total_employees >= 2:
        logger.info(f"🔄 Retraining SVM model with {total_employees} active employees...")
        try:
            train_result = face_service.train_svm_classifier()
            logger.info(f"✅ SVM model retrained: {train_result['num_employees']} employees, "
                       f"accuracy: {train_result['accuracy']:.3f}")
        except Exception as train_error:
            logger.warning(f"⚠️ SVM retraining failed: {train_error}")
    else:
        logger.info(f"ℹ️ Only {total_employees} active employee(s). SVM model not retrained.")
    
    return {"success": True, "message": "Employee deleted successfully"}
