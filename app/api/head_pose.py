"""
Head Pose Detection API
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import base64
import numpy as np
import cv2
from loguru import logger

from app.services.face_recognition import face_service
from app.services.head_pose import HeadPoseEstimator

router = APIRouter(prefix="/head-pose", tags=["head-pose"])
head_pose_estimator = HeadPoseEstimator()


class HeadPoseRequest(BaseModel):
    image: str  # Base64 encoded image


class HeadPoseResponse(BaseModel):
    current_pose: str
    message: str
    yaw: float
    pitch: float
    roll: float


@router.post("/detect", response_model=HeadPoseResponse)
async def detect_head_pose(request: HeadPoseRequest):
    """
    Detect head pose from image
    Returns current pose (center, left, right, up, down) and guidance message
    """
    try:
        # Decode base64 image
        image_data = request.image.split(',')[1] if ',' in request.image else request.image
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image data"
            )
        
        # Detect faces
        faces = face_service.detect_faces(frame)
        
        if len(faces) == 0:
            return HeadPoseResponse(
                current_pose="none",
                message="❌ Không phát hiện khuôn mặt. Hãy nhìn vào camera!",
                yaw=0.0,
                pitch=0.0,
                roll=0.0
            )
        
        if len(faces) > 1:
            return HeadPoseResponse(
                current_pose="multiple",
                message="⚠️ Phát hiện nhiều khuôn mặt. Chỉ một người trong khung hình!",
                yaw=0.0,
                pitch=0.0,
                roll=0.0
            )
        
        # Get face landmarks
        face = faces[0]
        landmarks = face.get('kps')  # Key points from InsightFace
        
        if landmarks is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to extract facial landmarks"
            )
        
        # Calculate head pose
        height, width = frame.shape[:2]
        yaw, pitch, roll, success = head_pose_estimator.get_head_pose(
            landmarks, width, height
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to calculate head pose"
            )
        
        # Determine current pose
        current_pose, message = _classify_pose(yaw, pitch)
        
        return HeadPoseResponse(
            current_pose=current_pose,
            message=message,
            yaw=yaw,
            pitch=pitch,
            roll=roll
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting head pose: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect head pose: {str(e)}"
        )


def _classify_pose(yaw: float, pitch: float) -> tuple[str, str]:
    """
    Classify pose based on yaw and pitch angles
    
    Args:
        yaw: Left/Right rotation (negative=left, positive=right)
        pitch: Up/Down rotation (negative=down, positive=up)
        
    Returns:
        Tuple of (pose_name, guidance_message)
    """
    # Thresholds for pose detection
    YAW_THRESHOLD = 20.0
    PITCH_THRESHOLD = 15.0
    
    # Priority: Check extreme poses first
    if abs(yaw) > YAW_THRESHOLD:
        if yaw < 0:
            return "left", "📸 Giữ nguyên - Quay TRÁI"
        else:
            return "right", "📸 Giữ nguyên - Quay PHẢI"
    
    if abs(pitch) > PITCH_THRESHOLD:
        if pitch > 0:
            return "up", "📸 Giữ nguyên - Ngẩng LÊN"
        else:
            return "down", "📸 Giữ nguyên - Cúi XUỐNG"
    
    # Default: center pose
    return "center", "📸 Giữ nguyên - Nhìn THẲNG"
