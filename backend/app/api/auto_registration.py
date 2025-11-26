"""
Auto Registration API Endpoints
WebSocket-based multi-angle face capture for employee registration
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
import cv2
import numpy as np
import base64
import json
import time
import asyncio
from typing import Optional
from loguru import logger

from app.core.database import get_db
from app.models.schemas import (
    AutoRegistrationStartRequest,
    AutoRegistrationProgressResponse,
    AutoRegistrationCompleteRequest,
    AutoRegistrationCompleteResponse
)
from app.services.auto_registration import auto_registration_service
from app.services.face_recognition import face_service
from app.services.employee import employee_service
from app.services.camera import camera_service

router = APIRouter(prefix="/auto-registration", tags=["auto-registration"])


@router.post("/start")
async def start_auto_registration(
    request: AutoRegistrationStartRequest,
    db: Session = Depends(get_db)
):
    """
    Start a new auto registration session
    """
    try:
        # Check if employee code already exists
        existing = employee_service.get_employee_by_code(db, request.employee_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Employee code {request.employee_code} already exists"
            )
        
        # Start session
        session = auto_registration_service.start_session(request.employee_code)
        
        return {
            "success": True,
            "message": "Auto registration session started",
            "session_id": session.session_id,
            "employee_code": request.employee_code,
            "progress": session.get_progress()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting auto registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/progress/{employee_code}", response_model=AutoRegistrationProgressResponse)
async def get_registration_progress(employee_code: str):
    """
    Get progress of current registration session
    """
    try:
        session = auto_registration_service.get_session(employee_code)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active registration session found"
            )
        
        return session.get_progress()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.websocket("/ws/capture/{employee_code}")
async def websocket_auto_capture(
    websocket: WebSocket,
    employee_code: str
):
    """
    WebSocket endpoint for real-time auto capture
    Streams camera feed and automatically captures when pose is correct
    """
    await websocket.accept()
    logger.info(f"WebSocket auto registration connected: {employee_code}")
    
    try:
        # Get session
        session = auto_registration_service.get_session(employee_code)
        
        if not session:
            await websocket.send_json({
                "type": "error",
                "message": "No active registration session. Please start a session first."
            })
            await websocket.close()
            return
        
        # Open camera
        if not camera_service.open_camera():
            await websocket.send_json({
                "type": "error",
                "message": "Failed to open camera"
            })
            await websocket.close()
            return
        
        await websocket.send_json({
            "type": "info",
            "message": f"Camera opened. Starting auto capture for {employee_code}",
            "progress": session.get_progress()
        })
        
        frame_count = 0
        last_process_time = time.time()
        target_fps = 10  # Process only 10 frames per second
        
        while True:
            try:
                # Control FPS to reduce processing load
                current_time = time.time()
                if current_time - last_process_time < 1.0 / target_fps:
                    await asyncio.sleep(0.01)
                    continue
                last_process_time = current_time
                
                # Read frame from camera
                frame = camera_service.read_frame()
                
                if frame is None:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Failed to read frame from camera"
                    })
                    break
                
                frame_count += 1
                
                # Detect faces
                faces = face_service.detect_faces(frame)
                
                if len(faces) == 0:
                    # No face detected
                    await websocket.send_json({
                        "type": "guidance",
                        "status": "no_face",
                        "message": "No face detected",
                        "guidance": "Please position your face in front of the camera",
                        "frame_count": frame_count,
                        "yaw": 0.0,
                        "pitch": 0.0,
                        "roll": 0.0,
                        "pose_ok": False
                    })
                elif len(faces) > 1:
                    # Multiple faces
                    await websocket.send_json({
                        "type": "guidance",
                        "status": "multiple_faces",
                        "message": "Multiple faces detected",
                        "guidance": "Please ensure only one person is in frame",
                        "frame_count": frame_count,
                        "yaw": 0.0,
                        "pitch": 0.0,
                        "roll": 0.0,
                        "pose_ok": False
                    })
                else:
                    # Single face detected - process it
                    face = faces[0]
                    bbox = face.bbox.astype(int).tolist()
                    
                    # Get keypoints (5 points from detection: left_eye, right_eye, nose, left_mouth, right_mouth)
                    landmarks = face.kps if hasattr(face, 'kps') else None
                    
                    if landmarks is None:
                        logger.warning("No keypoints found in face detection")
                    
                    # Process frame with session
                    result = session.process_frame(frame, bbox, landmarks)
                    
                    # Add frame count
                    result["frame_count"] = frame_count
                    
                    # Send result
                    await websocket.send_json({
                        "type": "guidance",
                        **result
                    })
                    
                    # Check if registration complete
                    if session.is_complete():
                        await websocket.send_json({
                            "type": "complete",
                            "message": "All poses captured! Registration ready to finalize.",
                            "progress": session.get_progress(),
                            "captured_images": session.get_captured_images()
                        })
                        break
                
                # Optionally send frame preview (every 10th frame to reduce bandwidth)
                if frame_count % 10 == 0:
                    # Resize frame for preview (reduce size by 50%)
                    h, w = frame.shape[:2]
                    preview_frame = cv2.resize(frame, (w // 2, h // 2))
                    
                    # Encode frame to JPEG with lower quality
                    _, buffer = cv2.imencode('.jpg', preview_frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    await websocket.send_json({
                        "type": "frame",
                        "image": frame_base64,
                        "frame_count": frame_count
                    })
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {employee_code}")
                break
            except Exception as e:
                logger.error(f"Error processing frame: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                break
        
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    finally:
        camera_service.release_camera()
        logger.info(f"WebSocket auto registration closed: {employee_code}")


@router.post("/complete", response_model=AutoRegistrationCompleteResponse)
async def complete_auto_registration(
    request: AutoRegistrationCompleteRequest,
    db: Session = Depends(get_db)
):
    """
    Finalize auto registration - process captured images and create employee
    """
    try:
        # Get session
        session = auto_registration_service.get_session(request.employee_code)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active registration session found"
            )
        
        if not session.is_complete():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration not complete. {len(session.captured_poses)}/{len(session.REQUIRED_POSES)} poses captured."
            )
        
        # Get captured images
        image_paths = session.get_captured_images()
        
        if not image_paths:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No images captured"
            )
        
        logger.info(f"Processing {len(image_paths)} images for {request.employee_code}")
        
        # Process images to extract embeddings
        all_embeddings = []
        
        for img_path in image_paths:
            img = cv2.imread(img_path)
            if img is None:
                logger.warning(f"Failed to read image: {img_path}")
                continue
            
            # Detect face and extract embedding
            faces = face_service.detect_faces(img)
            
            if len(faces) > 0:
                face = faces[0]
                embedding = face_service.app.get(img, face)[0].normed_embedding
                all_embeddings.append(embedding.tolist())
            else:
                logger.warning(f"No face detected in: {img_path}")
        
        if not all_embeddings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to extract embeddings from captured images"
            )
        
        # Calculate mean embedding
        mean_embedding = np.mean(all_embeddings, axis=0).tolist()
        
        logger.info(f"Extracted {len(all_embeddings)} embeddings for {request.employee_code}")
        
        # Create employee record (you'll need to pass full employee data)
        # For now, create with minimal data
        from app.models.schemas import EmployeeCreate
        
        employee_data = EmployeeCreate(
            employee_code=request.employee_code,
            full_name=request.employee_code,  # Should be passed from frontend
            email=None,
            phone_number=None,
            position=None
        )
        
        # Create employee in database
        db_employee = employee_service.create_employee(
            db=db,
            employee_data=employee_data,
            embeddings=all_embeddings,
            mean_embedding=mean_embedding,
            image_paths=image_paths
        )
        
        # End session
        auto_registration_service.end_session(request.employee_code)
        
        logger.info(f"✅ Auto registration completed for {request.employee_code}")
        
        return {
            "success": True,
            "message": "Employee registered successfully",
            "employee_id": db_employee.id,
            "total_images": len(image_paths),
            "embeddings_count": len(all_embeddings)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/cancel/{employee_code}")
async def cancel_auto_registration(employee_code: str):
    """
    Cancel active registration session
    """
    try:
        success = auto_registration_service.end_session(employee_code)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active registration session found"
            )
        
        return {
            "success": True,
            "message": "Registration session cancelled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/active-sessions")
async def get_active_sessions():
    """
    Get list of all active registration sessions
    """
    try:
        sessions = auto_registration_service.get_all_active_sessions()
        
        return {
            "success": True,
            "active_sessions": sessions,
            "count": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
