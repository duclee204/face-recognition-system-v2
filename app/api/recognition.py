"""
Recognition API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import cv2
import numpy as np
import base64
from datetime import datetime
from typing import List
from loguru import logger
import asyncio
import json
import time
import threading
from queue import Queue

from app.core.database import get_db
from app.models.schemas import (
    RecognitionRequest, RecognitionResponse, RecognizedFace
)
from app.services.face_recognition import face_service
from app.services.employee import employee_service
from app.services.attendance import attendance_service
from app.services.camera import camera_service

router = APIRouter(prefix="/recognition", tags=["recognition"])


@router.post("/recognize", response_model=RecognitionResponse)
async def recognize_faces(
    request: RecognitionRequest,
    db: Session = Depends(get_db)
):
    """
    Recognize faces in a single frame
    
    Client sends base64 encoded image
    """
    try:
        start_time = datetime.now()
        
        # Decode base64 image
        img_data = base64.b64decode(
            request.frame_data.split(',')[1] if ',' in request.frame_data else request.frame_data
        )
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image data"
            )
        
        # Recognize faces
        results = face_service.recognize_faces_in_frame(frame, request.threshold)
        
        # Convert to response format
        recognized_faces = []
        for result in results:
            employee_code = result['employee_code']
            
            # Get employee info from database
            employee = employee_service.get_employee_by_code(db, employee_code)
            
            if employee:
                recognized_faces.append(RecognizedFace(
                    employee_id=employee.id,
                    employee_code=employee.employee_code,
                    employee_name=employee.full_name,
                    confidence_score=result['confidence_score'],
                    recognition_method=result['method'],
                    bbox=result['bbox']
                ))
                
                # Log attendance - automatically handles check-in or check-out
                attendance_record, action = attendance_service.log_attendance(
                    db=db,
                    employee_id=employee.id
                )
                logger.info(f"🔔 {action.upper()}: {employee.full_name}")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return RecognitionResponse(
            success=True,
            faces=recognized_faces,
            processing_time=processing_time,
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recognition error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.websocket("/ws/stream")
async def websocket_recognition_stream(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time face recognition stream
    SMOOTH VERSION - Recognition runs in background thread
    Supports camera switching via WebSocket messages
    """
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        # Load models
        face_service.load_employee_db()
        face_service.load_svm_model()
        
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
            "message": f"Camera {camera_service.camera_id} stream started"
        })
        
        # Shared variables between threads
        frame_queue = Queue(maxsize=2)  # Queue for frames to process
        latest_results = []  # Latest recognition results (cleared each time)
        employee_cache = {}  # Cache employee data to avoid repeated DB queries
        results_lock = threading.Lock()
        is_running = threading.Event()
        is_running.set()
        
        # Background AI processing thread
        def ai_worker():
            """Background thread for face recognition"""
            while is_running.is_set():
                try:
                    if not frame_queue.empty():
                        frame = frame_queue.get(timeout=0.1)
                        temp_results = []
                        
                        # Detect faces
                        faces = face_service.detect_faces(frame)
                        
                        for face in faces:
                            try:
                                bbox = face.bbox.astype(int).tolist()
                                
                                # Recognize with 80% threshold
                                employee_code, confidence_score, method = face_service.recognize_face(
                                    face, 
                                    threshold=0.8  # 80% threshold for Unknown detection
                                )
                                
                                if employee_code is not None:
                                    # Known employee - get from cache or DB
                                    with results_lock:
                                        if employee_code not in employee_cache:
                                            employee = employee_service.get_employee_by_code(db, employee_code)
                                            if employee:
                                                employee_cache[employee_code] = employee
                                        else:
                                            employee = employee_cache[employee_code]
                                    
                                    if employee:
                                        result = {
                                            "employee_id": employee.id,
                                            "employee_code": employee.employee_code,
                                            "employee_name": employee.full_name,
                                            "confidence_score": float(confidence_score),
                                            "recognition_method": method,
                                            "bbox": bbox
                                        }
                                        
                                        temp_results.append(result)
                                        
                                        # Log attendance - continuously update check-out
                                        try:
                                            attendance_record, action = attendance_service.log_attendance(
                                                db=db,
                                                employee_id=employee.id
                                            )
                                            logger.info(f"🔔 {action.upper()}: {employee.full_name}")
                                        except Exception as att_error:
                                            logger.error(f"Error logging attendance: {att_error}")
                                else:
                                    # Unknown face (confidence < 80%)
                                    result = {
                                        "employee_id": None,
                                        "employee_code": "Unknown",
                                        "employee_name": "Unknown",
                                        "confidence_score": float(confidence_score),
                                        "recognition_method": method,
                                        "bbox": bbox
                                    }
                                    temp_results.append(result)
                                    
                            except Exception as face_error:
                                logger.error(f"Error recognizing face: {face_error}")
                                continue
                        
                        # Update latest results (thread-safe)
                        with results_lock:
                            latest_results.clear()
                            latest_results.extend(temp_results)
                    else:
                        time.sleep(0.01)  # Use time.sleep, not await
                        
                except Exception as e:
                    logger.error(f"Error in AI worker: {e}")
                    time.sleep(0.1)  # Use time.sleep, not await
        
        # Start AI thread
        ai_thread = threading.Thread(target=ai_worker, daemon=True)
        ai_thread.start()
        logger.info("🤖 AI worker thread started")
        
        # Main loop - just read camera and send frames
        frame_count = 0
        last_send_time = datetime.now()
        
        # Task to receive messages from client
        async def receive_messages():
            """Handle incoming WebSocket messages"""
            try:
                while True:
                    # Receive message from client
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get("type") == "switch_camera":
                        camera_id = message.get("camera_id")
                        logger.info(f"Switching to camera {camera_id}")
                        
                        # Switch camera
                        success = camera_service.switch_camera(camera_id)
                        
                        if success:
                            await websocket.send_json({
                                "type": "camera_switched",
                                "camera_id": camera_id,
                                "message": f"Switched to camera {camera_id}"
                            })
                        else:
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Failed to switch to camera {camera_id}"
                            })
                    
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected in receive_messages")
            except Exception as e:
                logger.error(f"Error in receive_messages: {e}")
        
        # Start message receiver task
        receive_task = asyncio.create_task(receive_messages())
        
        while True:
            try:
                # Read frame from camera
                frame = camera_service.read_frame()
                
                if frame is None:
                    await asyncio.sleep(0.01)
                    continue
                
                # Send frame to AI worker every 1 second
                current_time = datetime.now()
                if (current_time - last_send_time).total_seconds() >= 1.0:
                    if frame_queue.qsize() < 2:
                        frame_queue.put(frame.copy())
                        last_send_time = current_time
                
                # Get latest results (thread-safe)
                recognized_faces = []
                with results_lock:
                    recognized_faces = latest_results.copy()
                
                frame_count += 1
                
                # Encode frame as JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 100])
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # Send frame and results
                await websocket.send_json({
                    "type": "frame",
                    "frame": frame_base64,
                    "faces": recognized_faces,
                    "timestamp": datetime.now().isoformat(),
                    "frame_count": frame_count,
                    "camera_id": camera_service.camera_id
                })
                
                # Control frame rate (~30 FPS)
                await asyncio.sleep(0.033)
                
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected by client")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket loop: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                await asyncio.sleep(0.1)
        
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
        # Cancel receive task
        if 'receive_task' in locals():
            receive_task.cancel()
        
        # Stop AI worker thread
        is_running.clear()
        ai_thread.join(timeout=2)
        logger.info("AI worker thread stopped")
        
        # Close camera
        camera_service.close_camera()
        logger.info("WebSocket connection closed")


@router.get("/camera/info")
async def get_camera_info():
    """Get camera information"""
    try:
        if not camera_service.cap or not camera_service.cap.isOpened():
            camera_service.open_camera()
        
        info = camera_service.get_camera_info()
        camera_service.close_camera()
        
        return info
    except Exception as e:
        logger.error(f"Error getting camera info: {e}")
        return {"available": False, "error": str(e)}


@router.get("/camera/list")
async def list_cameras():
    """Get list of all available cameras"""
    try:
        cameras = camera_service.list_available_cameras()
        return {
            "success": True,
            "cameras": cameras,
            "count": len(cameras)
        }
    except Exception as e:
        logger.error(f"Error listing cameras: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/recognized")
async def get_recognized_employees():
    """Get list of employees recognized in current session"""
    try:
        recognized = camera_service.get_recognized_employees()
        return {
            "success": True,
            "recognized": recognized,
            "count": len(recognized)
        }
    except Exception as e:
        logger.error(f"Error getting recognized employees: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
