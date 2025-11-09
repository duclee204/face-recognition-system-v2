"""
Configuration settings for the application
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Face Recognition System"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/face_recognition_db"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "face_recognition_db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Storage Paths
    STORAGE_PATH: str = "./app/storage"
    EMPLOYEE_IMAGES_PATH: str = "./app/storage/employee_images"
    MODELS_PATH: str = "./app/storage/models"
    INSIGHTFACE_MODEL_PATH: str = "./app/storage/insightface_models"
    
    # Face Recognition Settings
    RECOGNITION_THRESHOLD: float = 0.5
    AUGMENTATION_COUNT: int = 5
    SVM_KERNEL: str = "rbf"
    SVM_C: float = 10.0
    SVM_GAMMA: float = 0.1
    
    # Camera Settings
    CAMERA_WIDTH: int = 640
    CAMERA_HEIGHT: int = 480
    CAMERA_FPS: int = 30
    PREDICT_INTERVAL: int = 30  # frames
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:4200",
        "http://localhost:3000",
        "http://localhost:8080"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Create necessary directories
os.makedirs(settings.STORAGE_PATH, exist_ok=True)
os.makedirs(settings.EMPLOYEE_IMAGES_PATH, exist_ok=True)
os.makedirs(settings.MODELS_PATH, exist_ok=True)
os.makedirs(settings.INSIGHTFACE_MODEL_PATH, exist_ok=True)
