"""
Attendance log database model
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class AttendanceLog(Base):
    __tablename__ = "attendance_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    employee_code = Column(String(50), nullable=False, index=True)
    employee_name = Column(String(255), nullable=False)
    
    # Recognition details
    confidence_score = Column(Float, nullable=False)
    recognition_method = Column(String(20))  # 'svm' or 'cosine'
    
    # Image snapshot
    snapshot_path = Column(String(500))
    
    # Location (optional for future)
    location = Column(String(255))
    
    # Timestamps
    check_in_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationship
    employee = relationship("Employee", backref="attendance_logs")
    
    def __repr__(self):
        return f"<AttendanceLog(id={self.id}, employee={self.employee_name}, time={self.check_in_time})>"
