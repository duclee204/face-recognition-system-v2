"""
Face Recognition Service using InsightFace and SVM
"""
import cv2
import numpy as np
import joblib
import os
from typing import List, Tuple, Optional, Dict
from insightface.app import FaceAnalysis
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV
from sklearn.metrics.pairwise import cosine_similarity
import albumentations as A
from datetime import datetime
from loguru import logger

from app.core.config import settings


class FaceRecognitionService:
    """
    Service for face detection, embedding extraction, and recognition
    """
    
    def __init__(self):
        self.app: Optional[FaceAnalysis] = None
        self.svm_model: Optional[SVC] = None
        self.employee_db: Dict = {}
        self.model_loaded = False
        
        # Augmentation pipeline - LIGHT version
        self.transform = A.Compose([
            A.RandomBrightnessContrast(brightness_limit=0.1, contrast_limit=0.1, p=0.5),
            A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=15, val_shift_limit=10, p=0.3),
            A.GaussNoise(var_limit=(5, 15), p=0.2),
            A.Affine(scale=(0.95, 1.05), rotate=(-10, 10), translate_percent=0.03, p=0.4),
        ])
        
        self._load_insightface()
    
    def _load_insightface(self):
        """Load InsightFace model"""
        try:
            logger.info("Loading InsightFace model...")
            
            # Get absolute path to model directory
            import os
            root_path = os.path.abspath(settings.INSIGHTFACE_MODEL_PATH)
            logger.info(f"Root path: {root_path}")
            
            # Check if model files exist
            # InsightFace expects: root/models/antelopev2/*.onnx
            model_dir = os.path.join(root_path, "models", "antelopev2")
            if not os.path.exists(model_dir):
                raise FileNotFoundError(f"Model directory not found: {model_dir}")
            
            # Load FaceAnalysis - it will look for root/models/antelopev2
            # antelopev2 includes detection (with 5 keypoints) and recognition
            self.app = FaceAnalysis(
                name="antelopev2",
                root=root_path,
                providers=['CPUExecutionProvider'],
                allowed_modules=['detection', 'recognition']
            )
            self.app.prepare(ctx_id=-1, det_size=(640, 640))
            logger.info("✅ InsightFace model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load InsightFace: {e}")
            raise
    
    def detect_faces(self, image: np.ndarray) -> List:
        """
        Detect faces in image
        
        Args:
            image: BGR image as numpy array
            
        Returns:
            List of detected faces
        """
        if self.app is None:
            raise RuntimeError("InsightFace not loaded")
        
        return self.app.get(image)
    
    def extract_embedding(self, face) -> np.ndarray:
        """
        Extract normalized embedding from detected face
        
        Args:
            face: Detected face object from InsightFace
            
        Returns:
            Normalized embedding (512-dim vector)
        """
        embedding = face.embedding
        normalized = embedding / np.linalg.norm(embedding)
        return normalized
    
    def augment_image(self, image: np.ndarray) -> np.ndarray:
        """
        Apply augmentation to image
        
        Args:
            image: Input image
            
        Returns:
            Augmented image
        """
        augmented = self.transform(image=image)
        return augmented["image"]
    
    def process_registration_frames(
        self, 
        frames: List[np.ndarray],
        num_aug: int = None
    ) -> Tuple[List[np.ndarray], int]:
        """
        Process registration frames to extract embeddings
        
        Args:
            frames: List of video frames
            num_aug: Number of augmentations per frame
            
        Returns:
            (embeddings, successful_count)
        """
        if num_aug is None:
            num_aug = settings.AUGMENTATION_COUNT
        
        all_embeddings = []
        successful_frames = 0
        
        for idx, frame in enumerate(frames):
            try:
                # Detect face in original frame
                faces = self.detect_faces(frame)
                
                if len(faces) == 0:
                    logger.warning(f"No face detected in frame {idx}")
                    continue
                
                # Extract embedding from original
                base_embedding = self.extract_embedding(faces[0])
                all_embeddings.append(base_embedding)
                successful_frames += 1
                
                # Generate augmented embeddings
                for _ in range(num_aug):
                    try:
                        aug_frame = self.augment_image(frame)
                        aug_faces = self.detect_faces(aug_frame)
                        
                        if len(aug_faces) > 0:
                            aug_embedding = self.extract_embedding(aug_faces[0])
                            all_embeddings.append(aug_embedding)
                    except Exception as e:
                        logger.debug(f"Augmentation failed: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"Error processing frame {idx}: {e}")
                continue
        
        return all_embeddings, successful_frames
    
    def save_employee_embeddings(
        self,
        employee_code: str,
        embeddings: List[np.ndarray]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Save employee embeddings to database
        
        Args:
            employee_code: Employee code
            embeddings: List of embeddings
            
        Returns:
            (all_embeddings_array, mean_embedding)
        """
        embeddings_array = np.array(embeddings)
        
        # Calculate mean embedding
        mean_embedding = np.mean(embeddings_array, axis=0)
        mean_embedding = mean_embedding / np.linalg.norm(mean_embedding)
        
        # Update employee database
        self.employee_db[employee_code] = {
            "all": embeddings_array.tolist(),
            "mean": mean_embedding.tolist()
        }
        
        # Save to file
        self._save_employee_db()
        
        return embeddings_array, mean_embedding
    
    def _save_employee_db(self):
        """Save employee database to file"""
        db_path = os.path.join(settings.MODELS_PATH, "employee_db.joblib")
        joblib.dump(self.employee_db, db_path)
        logger.info(f"Employee database saved: {len(self.employee_db)} employees")
    
    def load_employee_db(self) -> bool:
        """Load employee database from file"""
        db_path = os.path.join(settings.MODELS_PATH, "employee_db.joblib")
        
        if os.path.exists(db_path):
            self.employee_db = joblib.load(db_path)
            logger.info(f"Loaded employee database: {len(self.employee_db)} employees")
            return True
        else:
            logger.warning("Employee database file not found")
            self.employee_db = {}
            return False
    
    def train_svm_classifier(self) -> Dict:
        """
        Train SVM classifier on all employee embeddings
        
        Returns:
            Training statistics
        """
        start_time = datetime.now()
        
        if len(self.employee_db) == 0:
            raise ValueError("No employees in database to train on")
        
        # Collect all embeddings and labels
        X, y = [], []
        for employee_code, data in self.employee_db.items():
            for emb in data["all"]:
                X.append(emb)
                y.append(employee_code)
        
        X = np.array(X)
        y = np.array(y)
        
        logger.info(f"Training SVM on {len(X)} samples from {len(set(y))} employees")
        
        # Grid search for best parameters
        param_grid = {
            "C": [1, 5, 10, 20],
            "gamma": [0.01, 0.05, 0.1, 0.2],
            "kernel": ["rbf"]
        }
        
        svc = SVC(probability=True, class_weight="balanced")
        grid = GridSearchCV(svc, param_grid, cv=3, n_jobs=-1, scoring="accuracy")
        grid.fit(X, y)
        
        best_params = grid.best_params_
        best_score = grid.best_score_
        
        logger.info(f"Best params: {best_params} | CV accuracy: {best_score:.3f}")
        
        # Train final model
        self.svm_model = SVC(**best_params, probability=True, class_weight="balanced")
        self.svm_model.fit(X, y)
        
        # Save model
        model_path = os.path.join(settings.MODELS_PATH, "face_classifier_svm.pkl")
        joblib.dump(self.svm_model, model_path)
        self.model_loaded = True
        
        training_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "best_params": best_params,
            "accuracy": float(best_score),
            "total_samples": len(X),
            "num_employees": len(set(y)),
            "training_time": training_time
        }
    
    def load_svm_model(self) -> bool:
        """Load trained SVM model"""
        model_path = os.path.join(settings.MODELS_PATH, "face_classifier_svm.pkl")
        
        if os.path.exists(model_path):
            self.svm_model = joblib.load(model_path)
            self.model_loaded = True
            logger.info("✅ SVM model loaded")
            return True
        else:
            logger.warning("SVM model file not found. Train model after adding 2+ employees.")
            self.model_loaded = False
            return False
    
    def recognize_face(
        self,
        face,
        threshold: float = None,
        use_cosine_fallback: bool = True
    ) -> Tuple[Optional[str], float, str]:
        """
        Recognize a detected face
        
        Args:
            face: Detected face from InsightFace
            threshold: Recognition threshold
            use_cosine_fallback: Use cosine similarity if SVM fails
            
        Returns:
            (employee_code, confidence_score, method)
        """
        if threshold is None:
            threshold = settings.RECOGNITION_THRESHOLD
        
        # Extract embedding
        embedding = self.extract_embedding(face)
        embedding = embedding.reshape(1, -1)
        
        best_employee = None
        best_score = 0.0
        method = "unknown"
        
        # Try SVM first
        if self.model_loaded and self.svm_model is not None:
            try:
                pred_code = self.svm_model.predict(embedding)[0]
                prob = np.max(self.svm_model.predict_proba(embedding))
                
                if prob > best_score:
                    best_employee = pred_code
                    best_score = prob
                    method = "svm"
                    
            except Exception as e:
                logger.warning(f"SVM prediction failed: {e}")
        
        # Cosine similarity fallback
        if use_cosine_fallback and len(self.employee_db) > 0:
            for employee_code, data in self.employee_db.items():
                try:
                    all_embs = np.array(data["all"])
                    similarities = cosine_similarity(all_embs, embedding).flatten()
                    max_sim = np.max(similarities)
                    
                    if max_sim > best_score:
                        best_employee = employee_code
                        best_score = max_sim
                        method = "cosine"
                        
                except Exception as e:
                    logger.warning(f"Cosine similarity failed for {employee_code}: {e}")
        
        # Check threshold
        if best_score < threshold:
            return None, best_score, method
        
        return best_employee, best_score, method
    
    def recognize_faces_in_frame(
        self,
        frame: np.ndarray,
        threshold: float = 0.8  # Set default threshold to 80%
    ) -> List[Dict]:
        """
        Recognize all faces in a frame
        
        Args:
            frame: Input image frame
            threshold: Recognition threshold (default: 0.8 = 80%)
            
        Returns:
            List of recognition results (includes Unknown faces)
        """
        faces = self.detect_faces(frame)
        results = []
        
        for face in faces:
            employee_code, score, method = self.recognize_face(face, threshold)
            
            bbox = [int(v) for v in face.bbox]
            
            # If below threshold or not recognized, mark as Unknown
            if employee_code is None:
                results.append({
                    "employee_code": "Unknown",
                    "employee_name": "Unknown",
                    "confidence_score": float(score),
                    "recognition_method": method,
                    "bbox": bbox
                })
            else:
                results.append({
                    "employee_code": employee_code,
                    "confidence_score": float(score),
                    "method": method,
                    "bbox": bbox
                })
        
        return results


# Global instance
face_service = FaceRecognitionService()
