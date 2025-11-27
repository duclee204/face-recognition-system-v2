"""
Attendance log database model
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, Float, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class AttendanceLog(Base):
    __tablename__ = "attendance"
    
    # SQLite compatible schema
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False, index=True)
    camera_id = Column(Integer)
    work_date = Column(Date)
    check_in = Column(DateTime)
    check_out = Column(DateTime)
    total_hours = Column(Float)
    status = Column(String(20))  # 'checked-in', 'completed', 'pending'
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationship
    employee = relationship("Employee", backref="attendance_logs")
    
    def __repr__(self):
        return f"<AttendanceLog(id={self.id}, employee_id={self.employee_id}, date={self.work_date})>"
