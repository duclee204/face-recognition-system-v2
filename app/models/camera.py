"""
Camera database model
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class Camera(Base):
    __tablename__ = "camera"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_code = Column(String(50), unique=True, index=True)
    camera_name = Column(String(100))
    ip_address = Column(String(50))
    location = Column(String(200))
    status = Column(String(20), default='active')  # 'active' or 'inactive'
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<Camera(id={self.id}, name={self.camera_name}, code={self.camera_code})>"
