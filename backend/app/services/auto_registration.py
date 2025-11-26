"""
Auto Registration Service
Manages multi-angle face capture for employee registration
"""
import os
import time
import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from loguru import logger

from app.services.head_pose import head_pose_estimator

# Configure OpenCV to use 4 threads for optimized performance
cv2.setNumThreads(4)


class AutoRegistrationSession:
    """
    Manages a single auto-registration session for one employee
    """
    
    # Required poses for complete registration
    REQUIRED_POSES = ["center", "left", "right", "up", "down"]
    
    # Number of frames to hold pose before capturing
    HOLD_FRAMES = 15  # ~0.5 seconds at 30fps
    
    def __init__(self, employee_code: str, storage_path: str):
        """
        Initialize registration session
        
        Args:
            employee_code: Employee code for this registration
            storage_path: Base path to store captured images
        """
        self.employee_code = employee_code
        self.storage_path = storage_path
        self.session_id = f"{employee_code}_{int(time.time())}"
        
        # Session state
        self.captured_poses: Dict[str, str] = {}  # pose -> image_path
        self.current_target_pose = "center"  # Start with center
        self.current_pose_index = 0
        
        # Frame counting for stability
        self.stable_frames = 0
        self.last_guidance = ""
        
        # Create storage directory
        self.session_dir = os.path.join(storage_path, employee_code, self.session_id)
        os.makedirs(self.session_dir, exist_ok=True)
        
        logger.info(f"Auto registration session started: {self.session_id}")
    
    def get_progress(self) -> Dict:
        """Get current progress"""
        return {
            "session_id": self.session_id,
            "employee_code": self.employee_code,
            "current_target_pose": self.current_target_pose,
            "captured_poses": list(self.captured_poses.keys()),
            "remaining_poses": [p for p in self.REQUIRED_POSES if p not in self.captured_poses],
            "progress_percentage": int(len(self.captured_poses) / len(self.REQUIRED_POSES) * 100),
            "is_complete": self.is_complete()
        }
    
    def is_complete(self) -> bool:
        """Check if all poses captured"""
        return len(self.captured_poses) >= len(self.REQUIRED_POSES)
    
    def process_frame(
        self,
        frame: np.ndarray,
        face_bbox: List[int],
        landmarks: np.ndarray
    ) -> Dict:
        """
        Process a frame and check if it should be captured
        
        Args:
            frame: Video frame
            face_bbox: Face bounding box [x1, y1, x2, y2]
            landmarks: Facial landmarks
            
        Returns:
            Dict with processing result and guidance
        """
        if self.is_complete():
            return {
                "status": "completed",
                "message": "All poses captured!",
                "should_capture": False,
                "pose_ok": False,
                "guidance": "Registration complete!"
            }
        
        # Calculate head pose
        h, w = frame.shape[:2]
        yaw, pitch, roll, success = head_pose_estimator.get_head_pose(landmarks, w, h)
        
        if not success:
            return {
                "status": "no_pose",
                "message": "Cannot detect head pose",
                "should_capture": False,
                "pose_ok": False,
                "guidance": "Please face the camera clearly",
                "yaw": 0.0,
                "pitch": 0.0,
                "roll": 0.0
            }
        
        # Check if current pose is acceptable
        pose_ok, guidance = head_pose_estimator.is_pose_acceptable(
            yaw, pitch, roll,
            target_pose=self.current_target_pose
        )
        
        # Update guidance
        self.last_guidance = guidance
        
        if pose_ok:
            self.stable_frames += 1
            
            # Check if held long enough
            if self.stable_frames >= self.HOLD_FRAMES:
                # Capture this frame
                should_capture = True
                self.stable_frames = 0
                
                # Save image
                image_path = self._save_frame(frame, face_bbox)
                self.captured_poses[self.current_target_pose] = image_path
                
                # Move to next pose
                self._advance_to_next_pose()
                
                return {
                    "status": "captured",
                    "message": f"Captured {self.current_target_pose} pose!",
                    "should_capture": True,
                    "pose_ok": True,
                    "guidance": guidance,
                    "image_path": image_path,
                    "captured_pose": list(self.captured_poses.keys())[-1],
                    "yaw": float(yaw),
                    "pitch": float(pitch),
                    "roll": float(roll),
                    "progress": self.get_progress()
                }
            else:
                # Still holding
                frames_remaining = self.HOLD_FRAMES - self.stable_frames
                return {
                    "status": "holding",
                    "message": f"Hold steady... {frames_remaining}",
                    "should_capture": False,
                    "pose_ok": True,
                    "guidance": f"{guidance} ({frames_remaining} frames left)",
                    "stable_frames": self.stable_frames,
                    "hold_frames_required": self.HOLD_FRAMES,
                    "yaw": float(yaw),
                    "pitch": float(pitch),
                    "roll": float(roll)
                }
        else:
            # Reset counter if pose not OK
            self.stable_frames = 0
            
            return {
                "status": "adjusting",
                "message": "Adjust your pose",
                "should_capture": False,
                "pose_ok": False,
                "guidance": guidance,
                "yaw": float(yaw),
                "pitch": float(pitch),
                "roll": float(roll),
                "target_pose": self.current_target_pose
            }
    
    def _save_frame(self, frame: np.ndarray, face_bbox: List[int]) -> str:
        """
        Save captured frame
        
        Args:
            frame: Video frame
            face_bbox: Face bounding box
            
        Returns:
            Path to saved image
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{self.current_target_pose}_{timestamp}.jpg"
        filepath = os.path.join(self.session_dir, filename)
        
        # Optionally crop to face region (with margin)
        x1, y1, x2, y2 = face_bbox
        margin = 50
        h, w = frame.shape[:2]
        x1 = max(0, x1 - margin)
        y1 = max(0, y1 - margin)
        x2 = min(w, x2 + margin)
        y2 = min(h, y2 + margin)
        
        face_crop = frame[y1:y2, x1:x2]
        
        # Save full frame and cropped face
        cv2.imwrite(filepath, face_crop)
        
        logger.info(f"Saved {self.current_target_pose} pose: {filepath}")
        return filepath
    
    def _advance_to_next_pose(self):
        """Move to next required pose"""
        self.current_pose_index += 1
        
        if self.current_pose_index < len(self.REQUIRED_POSES):
            self.current_target_pose = self.REQUIRED_POSES[self.current_pose_index]
            logger.info(f"Advanced to pose: {self.current_target_pose}")
        else:
            logger.info("All poses captured!")
    
    def get_captured_images(self) -> List[str]:
        """Get list of all captured image paths"""
        return list(self.captured_poses.values())
    
    def cleanup(self):
        """Clean up session resources"""
        logger.info(f"Cleaning up session: {self.session_id}")


class AutoRegistrationService:
    """
    Service to manage auto registration sessions
    """
    
    def __init__(self, storage_path: str = "./app/storage/employee_images"):
        self.storage_path = storage_path
        self.active_sessions: Dict[str, AutoRegistrationSession] = {}
    
    def start_session(self, employee_code: str) -> AutoRegistrationSession:
        """
        Start a new auto registration session
        
        Args:
            employee_code: Employee code
            
        Returns:
            AutoRegistrationSession object
        """
        # End existing session if any
        if employee_code in self.active_sessions:
            self.end_session(employee_code)
        
        session = AutoRegistrationSession(employee_code, self.storage_path)
        self.active_sessions[employee_code] = session
        
        return session
    
    def get_session(self, employee_code: str) -> Optional[AutoRegistrationSession]:
        """Get active session for employee"""
        return self.active_sessions.get(employee_code)
    
    def end_session(self, employee_code: str) -> bool:
        """
        End active session
        
        Args:
            employee_code: Employee code
            
        Returns:
            True if session existed and was ended
        """
        if employee_code in self.active_sessions:
            session = self.active_sessions[employee_code]
            session.cleanup()
            del self.active_sessions[employee_code]
            return True
        return False
    
    def get_all_active_sessions(self) -> List[str]:
        """Get list of all active session employee codes"""
        return list(self.active_sessions.keys())


# Global instance
auto_registration_service = AutoRegistrationService()
