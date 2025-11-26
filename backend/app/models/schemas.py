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
    full_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    position: Optional[str] = Field(None, max_length=100)
    base_salary: Optional[float] = None
    standard_work_days: Optional[int] = None
    department_id: Optional[int] = None


class EmployeeCreate(EmployeeBase):
    employee_code: str = Field(..., min_length=1, max_length=20)


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    position: Optional[str] = Field(None, max_length=100)
    base_salary: Optional[float] = None
    standard_work_days: Optional[int] = None
    department_id: Optional[int] = None
    status: Optional[str] = None


class EmployeeResponse(EmployeeBase):
    id: int
    employee_code: str
    total_embeddings: int
    status: Optional[str] = None
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
    work_date: Optional[datetime] = None
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    total_hours: Optional[float] = None
    status: Optional[str] = None
    confidence_score: Optional[float] = None
    recognition_method: Optional[str] = None
    camera_id: Optional[int] = None
    notes: Optional[str] = None
    
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
    model_config = {"protected_namespaces": ()}
    
    status: str
    total_employees: int
    model_loaded: bool
    insightface_loaded: bool
    camera_available: bool
    last_trained: Optional[datetime] = None


class TrainModelRequest(BaseModel):
    force_retrain: bool = False


class TrainModelResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
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


# ============================================
# Auto Registration Schemas
# ============================================

class AutoRegistrationStartRequest(BaseModel):
    employee_code: str = Field(..., min_length=1, max_length=20)
    full_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    position: Optional[str] = None


class AutoRegistrationProgressResponse(BaseModel):
    session_id: str
    employee_code: str
    current_target_pose: str
    captured_poses: List[str]
    remaining_poses: List[str]
    progress_percentage: int
    is_complete: bool


class AutoRegistrationFrameResponse(BaseModel):
    status: str  # 'adjusting', 'holding', 'captured', 'completed', 'no_pose'
    message: str
    guidance: str
    pose_ok: bool
    should_capture: bool
    target_pose: Optional[str] = None
    captured_pose: Optional[str] = None
    yaw: Optional[float] = None
    pitch: Optional[float] = None
    roll: Optional[float] = None
    stable_frames: Optional[int] = None
    hold_frames_required: Optional[int] = None
    progress: Optional[AutoRegistrationProgressResponse] = None


class AutoRegistrationCompleteRequest(BaseModel):
    employee_code: str
    session_id: str


class AutoRegistrationCompleteResponse(BaseModel):
    success: bool
    message: str
    employee_id: Optional[int] = None
    total_images: int
    embeddings_count: int

    timestamp: Optional[float] = None


class CameraStreamRequest(BaseModel):
    camera_id: int = 0
    enable_recognition: bool = True
    threshold: float = 0.5
