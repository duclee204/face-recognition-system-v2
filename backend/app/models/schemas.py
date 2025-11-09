"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


# ============================================
# Employee Schemas
# ============================================

class EmployeeBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)


class EmployeeCreate(EmployeeBase):
    employee_code: str = Field(..., min_length=1, max_length=50)


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class EmployeeResponse(EmployeeBase):
    id: int
    employee_code: str
    total_embeddings: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EmployeeListResponse(BaseModel):
    total: int
    employees: List[EmployeeResponse]


# ============================================
# Registration Schemas
# ============================================

class RegistrationStartRequest(BaseModel):
    employee_code: str = Field(..., min_length=1, max_length=50)
    full_name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None


class RegistrationFrameData(BaseModel):
    frame_data: str  # Base64 encoded image
    frame_number: int
    timestamp: float


class RegistrationCompleteRequest(BaseModel):
    session_id: str


class RegistrationResponse(BaseModel):
    success: bool
    message: str
    session_id: Optional[str] = None
    employee_id: Optional[int] = None
    total_embeddings: Optional[int] = None
    processing_time: Optional[float] = None


# ============================================
# Recognition Schemas
# ============================================

class RecognitionRequest(BaseModel):
    frame_data: str  # Base64 encoded image
    threshold: Optional[float] = Field(default=0.5, ge=0.0, le=1.0)


class RecognizedFace(BaseModel):
    employee_id: int
    employee_code: str
    employee_name: str
    confidence_score: float
    recognition_method: str  # 'svm' or 'cosine'
    bbox: List[int]  # [x1, y1, x2, y2]


class RecognitionResponse(BaseModel):
    success: bool
    faces: List[RecognizedFace]
    processing_time: float
    timestamp: datetime


# ============================================
# Attendance Schemas
# ============================================

class AttendanceLogResponse(BaseModel):
    id: int
    employee_id: int
    employee_code: str
    employee_name: str
    confidence_score: float
    recognition_method: str
    check_in_time: datetime
    
    class Config:
        from_attributes = True


class AttendanceListResponse(BaseModel):
    total: int
    logs: List[AttendanceLogResponse]


class AttendanceStatsResponse(BaseModel):
    total_today: int
    total_this_week: int
    total_this_month: int
    unique_employees_today: int


# ============================================
# System Schemas
# ============================================

class SystemStatusResponse(BaseModel):
    status: str
    total_employees: int
    model_loaded: bool
    insightface_loaded: bool
    camera_available: bool
    last_trained: Optional[datetime] = None


class TrainModelRequest(BaseModel):
    force_retrain: bool = False


class TrainModelResponse(BaseModel):
    success: bool
    message: str
    training_time: Optional[float] = None
    model_accuracy: Optional[float] = None
    total_samples: Optional[int] = None


# ============================================
# WebSocket Schemas
# ============================================

class WebSocketMessage(BaseModel):
    type: str  # 'frame', 'recognition', 'error', 'info'
    data: dict
    timestamp: Optional[float] = None


class CameraStreamRequest(BaseModel):
    camera_id: int = 0
    enable_recognition: bool = True
    threshold: float = 0.5
