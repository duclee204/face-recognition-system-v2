"""
Employee database model
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.sql import func
from app.core.database import Base


class Employee(Base):
    __tablename__ = "employee"
    
    # SQLite compatible schema
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_code = Column(String(20), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False, index=True)
    email = Column(String(100), unique=True, index=True)
    phone_number = Column(String(20))
    position = Column(String(100))
    base_salary = Column(Float)
    standard_work_days = Column(Integer)
    status = Column(String(20), default='active')  # 'active' or 'inactive'
    department_id = Column(Integer)
    
    # Face recognition fields
    embeddings = Column(Text)  # JSON array of embeddings
    mean_embedding = Column(Text)  # Mean embedding
    image_paths = Column(Text)  # JSON array of image paths
    total_embeddings = Column(Integer, default=0)
    registration_video_path = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f"<Employee(id={self.id}, name={self.full_name}, code={self.employee_code})>"
