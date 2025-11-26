"""
Head Pose Estimation Service
Calculates yaw, pitch, roll from facial landmarks
"""
import numpy as np
import cv2
from typing import Tuple, Optional
from loguru import logger


class HeadPoseEstimator:
    """
    Estimate head pose (yaw, pitch, roll) from facial landmarks
    """
    
    def __init__(self):
        # 3D model points of facial landmarks (generic face model)
        self.model_points = np.array([
            (0.0, 0.0, 0.0),             # Nose tip
            (0.0, -330.0, -65.0),        # Chin
            (-225.0, 170.0, -135.0),     # Left eye left corner
            (225.0, 170.0, -135.0),      # Right eye right corner
            (-150.0, -150.0, -125.0),    # Left mouth corner
            (150.0, -150.0, -125.0)      # Right mouth corner
        ], dtype=np.float64)
        
    def get_head_pose(
        self, 
        landmarks: np.ndarray,
        image_width: int,
        image_height: int
    ) -> Tuple[float, float, float, bool]:
        """
        Calculate head pose angles from facial landmarks
        
        Args:
            landmarks: Facial landmarks array (shape: [N, 2] or [N, 3])
            image_width: Image width
            image_height: Image height
            
        Returns:
            Tuple of (yaw, pitch, roll, success)
            - yaw: Left/Right rotation (-90 to 90, negative=left, positive=right)
            - pitch: Up/Down rotation (-90 to 90, negative=down, positive=up)
            - roll: Tilt rotation (-180 to 180)
            - success: True if calculation successful
        """
        try:
            # Check if landmarks is None or empty
            if landmarks is None or len(landmarks) == 0:
                return 0.0, 0.0, 0.0, False
            # Camera matrix (approximate intrinsic parameters)
            focal_length = image_width
            center = (image_width / 2, image_height / 2)
            camera_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1]
            ], dtype=np.float64)
            
            # Assume no lens distortion
            dist_coeffs = np.zeros((4, 1))
            
            # Select 6 key points from landmarks
            # InsightFace landmarks typically: 5 points or 106/68 points
            if len(landmarks) == 5:
                # 5-point landmarks: left_eye, right_eye, nose, left_mouth, right_mouth
                image_points = np.array([
                    landmarks[2],      # Nose tip
                    landmarks[2],      # Use nose as chin approximation
                    landmarks[0],      # Left eye
                    landmarks[1],      # Right eye
                    landmarks[3],      # Left mouth
                    landmarks[4]       # Right mouth
                ], dtype=np.float64)
            elif len(landmarks) >= 68:
                # 68-point or 106-point landmarks (dlib/insightface style)
                image_points = np.array([
                    landmarks[30],     # Nose tip (point 30)
                    landmarks[8],      # Chin (point 8)
                    landmarks[36],     # Left eye left corner
                    landmarks[45],     # Right eye right corner
                    landmarks[48],     # Left mouth corner
                    landmarks[54]      # Right mouth corner
                ], dtype=np.float64)
            else:
                # Use first 6 points if available
                image_points = landmarks[:6].astype(np.float64)
            
            # Solve PnP (Perspective-n-Point) to get rotation and translation vectors
            success, rotation_vector, translation_vector = cv2.solvePnP(
                self.model_points,
                image_points,
                camera_matrix,
                dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE
            )
            
            if not success:
                return 0.0, 0.0, 0.0, False
            
            # Convert rotation vector to rotation matrix
            rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
            
            # Calculate Euler angles from rotation matrix
            yaw, pitch, roll = self._rotation_matrix_to_euler_angles(rotation_matrix)
            
            return yaw, pitch, roll, True
            
        except Exception as e:
            logger.error(f"Error calculating head pose: {e}")
            return 0.0, 0.0, 0.0, False
    
    def _rotation_matrix_to_euler_angles(self, R: np.ndarray) -> Tuple[float, float, float]:
        """
        Convert rotation matrix to Euler angles (yaw, pitch, roll)
        
        Args:
            R: 3x3 rotation matrix
            
        Returns:
            Tuple of (yaw, pitch, roll) in degrees
        """
        # Calculate yaw (rotation around Y-axis)
        sy = np.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
        
        singular = sy < 1e-6
        
        if not singular:
            yaw = np.arctan2(R[1, 0], R[0, 0])
            pitch = np.arctan2(-R[2, 0], sy)
            roll = np.arctan2(R[2, 1], R[2, 2])
        else:
            yaw = np.arctan2(-R[1, 2], R[1, 1])
            pitch = np.arctan2(-R[2, 0], sy)
            roll = 0
        
        # Convert to degrees
        yaw = np.degrees(yaw)
        pitch = np.degrees(pitch)
        roll = np.degrees(roll)
        
        return yaw, pitch, roll
    
    def is_pose_acceptable(
        self,
        yaw: float,
        pitch: float,
        roll: float,
        target_pose: str = "center",
        yaw_threshold: float = 15.0,
        pitch_threshold: float = 15.0,
        roll_threshold: float = 15.0
    ) -> Tuple[bool, str]:
        """
        Check if head pose is acceptable for target pose
        
        Args:
            yaw: Yaw angle (left/right)
            pitch: Pitch angle (up/down)
            roll: Roll angle (tilt)
            target_pose: Target pose type: "center", "left", "right", "up", "down"
            yaw_threshold: Maximum deviation for yaw (degrees)
            pitch_threshold: Maximum deviation for pitch (degrees)
            roll_threshold: Maximum deviation for roll (degrees)
            
        Returns:
            Tuple of (is_acceptable, guidance_message)
        """
        if target_pose == "center":
            # Center pose: face forward, minimal yaw/pitch
            if abs(yaw) > yaw_threshold:
                direction = "left" if yaw < 0 else "right"
                return False, f"Turn face slightly {direction}"
            if abs(pitch) > pitch_threshold:
                direction = "down" if pitch < 0 else "up"
                return False, f"Tilt head slightly {direction}"
            if abs(roll) > roll_threshold:
                return False, "Keep head straight (don't tilt)"
            return True, "Perfect! Hold steady..."
            
        elif target_pose == "left":
            # Left pose: turn head left (negative yaw)
            if yaw > -20 or yaw < -50:
                if yaw > -20:
                    return False, "Turn head more to the LEFT"
                else:
                    return False, "Turn head less to the left"
            if abs(pitch) > pitch_threshold:
                return False, "Keep head level (don't look up/down)"
            if abs(roll) > roll_threshold:
                return False, "Keep head straight (don't tilt)"
            return True, "Perfect left angle! Hold steady..."
            
        elif target_pose == "right":
            # Right pose: turn head right (positive yaw)
            if yaw < 20 or yaw > 50:
                if yaw < 20:
                    return False, "Turn head more to the RIGHT"
                else:
                    return False, "Turn head less to the right"
            if abs(pitch) > pitch_threshold:
                return False, "Keep head level (don't look up/down)"
            if abs(roll) > roll_threshold:
                return False, "Keep head straight (don't tilt)"
            return True, "Perfect right angle! Hold steady..."
            
        elif target_pose == "up":
            # Up pose: tilt head up (positive pitch)
            if pitch < 10 or pitch > 35:
                if pitch < 10:
                    return False, "Tilt head UP more"
                else:
                    return False, "Tilt head down slightly"
            if abs(yaw) > yaw_threshold:
                return False, "Keep face forward (don't turn left/right)"
            if abs(roll) > roll_threshold:
                return False, "Keep head straight (don't tilt sideways)"
            return True, "Perfect up angle! Hold steady..."
            
        elif target_pose == "down":
            # Down pose: tilt head down (negative pitch)
            if pitch > -10 or pitch < -35:
                if pitch > -10:
                    return False, "Tilt head DOWN more"
                else:
                    return False, "Tilt head up slightly"
            if abs(yaw) > yaw_threshold:
                return False, "Keep face forward (don't turn left/right)"
            if abs(roll) > roll_threshold:
                return False, "Keep head straight (don't tilt sideways)"
            return True, "Perfect down angle! Hold steady..."
        
        return False, "Unknown target pose"


# Global instance
head_pose_estimator = HeadPoseEstimator()
