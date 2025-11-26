"""
Camera Service for real-time face recognition with multiprocessing
"""
import cv2
import numpy as np
from typing import Optional, Dict, List, Callable
from multiprocessing import Process, Queue, Manager, Event
import time
from datetime import datetime
from loguru import logger

from app.core.config import settings


class CameraService:
    """
    Service for camera streaming and real-time face recognition
    Uses multiprocessing for optimal performance (60 FPS)
    """
    
    def __init__(self, camera_id: int = 0):
        self.camera_id = camera_id
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        
        # Multiprocessing components
        self.frame_queue: Optional[Queue] = None
        self.result_queue: Optional[Queue] = None
        self.recognized_dict = None
        self.stop_event: Optional[Event] = None
        self.ai_process: Optional[Process] = None
    
    @staticmethod
    def list_available_cameras(max_cameras: int = 10) -> List[Dict]:
        """
        List all available cameras on the system
        
        Args:
            max_cameras: Maximum number of cameras to check
            
        Returns:
            List of camera information dictionaries
        """
        available_cameras = []
        
        for camera_id in range(max_cameras):
            try:
                cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
                if not cap.isOpened():
                    cap = cv2.VideoCapture(camera_id)
                
                if cap.isOpened():
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = int(cap.get(cv2.CAP_PROP_FPS))
                    backend = cap.getBackendName()
                    
                    available_cameras.append({
                        "id": camera_id,
                        "name": f"Camera {camera_id}",
                        "width": width,
                        "height": height,
                        "fps": fps if fps > 0 else 30,
                        "backend": backend
                    })
                    
                    cap.release()
                    logger.info(f"Found camera {camera_id}: {width}x{height}")
                    
            except Exception as e:
                logger.debug(f"Camera {camera_id} not available: {e}")
                continue
        
        return available_cameras
    
    def switch_camera(self, new_camera_id: int) -> bool:
        """
        Switch to a different camera
        
        Args:
            new_camera_id: ID of the new camera
            
        Returns:
            Success status
        """
        try:
            # Close current camera
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            
            # Update camera ID
            self.camera_id = new_camera_id
            
            # Open new camera
            success = self.open_camera()
            
            if success:
                logger.info(f"✅ Switched to camera {new_camera_id}")
            else:
                logger.error(f"❌ Failed to switch to camera {new_camera_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error switching camera: {e}")
            return False
    
    def open_camera(self) -> bool:
        """Open camera device"""
        try:
            self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
            
            if not self.cap.isOpened():
                logger.warning("Trying default backend...")
                self.cap = cv2.VideoCapture(self.camera_id)
            
            if not self.cap.isOpened():
                logger.error("Failed to open camera")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.CAMERA_HEIGHT)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Warm up camera
            for _ in range(10):
                self.cap.read()
            
            logger.info(f"✅ Camera {self.camera_id} opened successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error opening camera: {e}")
            return False
    
    def close_camera(self):
        """Close camera device"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            logger.info("Camera closed")
    
    def read_frame(self) -> Optional[np.ndarray]:
        """Read a single frame from camera"""
        if self.cap is None or not self.cap.isOpened():
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        return frame
    
    def get_camera_info(self) -> Dict:
        """Get camera information"""
        if self.cap is None or not self.cap.isOpened():
            return {"available": False}
        
        return {
            "available": True,
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": int(self.cap.get(cv2.CAP_PROP_FPS)),
            "backend": self.cap.getBackendName()
        }
    
    @staticmethod
    def ai_recognition_worker(
        frame_queue: Queue,
        result_queue: Queue,
        recognized_dict,
        stop_event: Event,
        threshold: float,
        callback: Optional[Callable] = None
    ):
        """
        AI recognition worker process (runs in separate process)
        
        Args:
            frame_queue: Queue to receive frames
            result_queue: Queue to send results
            recognized_dict: Shared dictionary for recognized employees
            stop_event: Event to stop the worker
            threshold: Recognition threshold
            callback: Optional callback function for each recognition
        """
        # Import inside worker to avoid pickling issues
        from app.services.face_recognition import face_service
        
        logger.info("🤖 AI Recognition Process Started")
        
        try:
            while not stop_event.is_set():
                try:
                    if not frame_queue.empty():
                        frame_data = frame_queue.get(timeout=0.1)
                        frame = frame_data['frame']
                        frame_id = frame_data['id']
                        
                        process_start = time.time()
                        
                        # Recognize faces in frame
                        results = face_service.recognize_faces_in_frame(frame, threshold)
                        
                        process_time = (time.time() - process_start) * 1000
                        
                        # Send results back
                        result_queue.put({
                            'frame_id': frame_id,
                            'results': results,
                            'process_time': process_time,
                            'num_faces': len(results)
                        })
                        
                        # Update recognized dictionary
                        for result in results:
                            employee_code = result['employee_code']
                            if employee_code not in recognized_dict:
                                recognized_dict[employee_code] = {
                                    'timestamp': datetime.now().isoformat(),
                                    'confidence': result['confidence_score'],
                                    'method': result['method']
                                }
                                
                                # Execute callback if provided
                                if callback:
                                    callback(result)
                                
                                logger.info(f"✅ Recognized: {employee_code} ({result['confidence_score']:.3f})")
                    
                    else:
                        time.sleep(0.01)
                        
                except Exception as e:
                    logger.error(f"AI worker error: {e}")
                    time.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"AI worker fatal error: {e}")
        
        logger.info("🛑 AI Recognition Process Stopped")
    
    def start_recognition_stream(
        self,
        threshold: float = None,
        predict_interval: float = 1.0,
        on_recognition: Optional[Callable] = None
    ) -> bool:
        """
        Start real-time recognition stream with multiprocessing
        
        Args:
            threshold: Recognition threshold
            predict_interval: Interval between predictions (seconds)
            on_recognition: Callback function for each recognition
            
        Returns:
            Success status
        """
        if threshold is None:
            threshold = settings.RECOGNITION_THRESHOLD
        
        if not self.open_camera():
            return False
        
        # Create multiprocessing components
        manager = Manager()
        self.frame_queue = Queue(maxsize=2)
        self.result_queue = Queue(maxsize=5)
        self.recognized_dict = manager.dict()
        self.stop_event = Event()
        
        # Start AI process
        self.ai_process = Process(
            target=self.ai_recognition_worker,
            args=(
                self.frame_queue,
                self.result_queue,
                self.recognized_dict,
                self.stop_event,
                threshold,
                on_recognition
            ),
            daemon=True
        )
        self.ai_process.start()
        self.is_running = True
        
        logger.info(f"✅ Recognition stream started (PID: {self.ai_process.pid})")
        return True
    
    def stop_recognition_stream(self):
        """Stop recognition stream"""
        self.is_running = False
        
        if self.stop_event:
            self.stop_event.set()
        
        if self.ai_process:
            self.ai_process.join(timeout=3)
            if self.ai_process.is_alive():
                self.ai_process.terminate()
                self.ai_process.join()
        
        self.close_camera()
        logger.info("Recognition stream stopped")
    
    def get_frame_with_recognition(
        self,
        send_for_recognition: bool = True
    ) -> Optional[Dict]:
        """
        Get frame with recognition results
        
        Args:
            send_for_recognition: Whether to send frame for recognition
            
        Returns:
            Dictionary with frame and recognition results
        """
        frame = self.read_frame()
        if frame is None:
            return None
        
        result = {
            'frame': frame,
            'results': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Send frame for recognition
        if send_for_recognition and self.frame_queue:
            if self.frame_queue.qsize() < 2:
                frame_id = int(time.time() * 1000)
                self.frame_queue.put({
                    'frame': frame.copy(),
                    'id': frame_id
                })
        
        # Get recognition results
        if self.result_queue:
            while not self.result_queue.empty():
                try:
                    recognition_data = self.result_queue.get_nowait()
                    result['results'] = recognition_data['results']
                    result['process_time'] = recognition_data['process_time']
                except:
                    pass
        
        return result
    
    def get_recognized_employees(self) -> Dict:
        """Get dictionary of recognized employees"""
        if self.recognized_dict is None:
            return {}
        return dict(self.recognized_dict)


# Global instance
camera_service = CameraService()
