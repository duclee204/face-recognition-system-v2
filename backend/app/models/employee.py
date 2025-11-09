"""
Employee database model
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_code = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(20))
    department = Column(String(100))
    position = Column(String(100))
    
    # Face embeddings stored as JSON string
    embeddings = Column(Text, nullable=False)  # JSON array of embeddings
    mean_embedding = Column(Text, nullable=False)  # Mean embedding
    
    # Image paths
    image_paths = Column(Text)  # JSON array of image paths
    
    # Metadata
    total_embeddings = Column(Integer, default=0)
    registration_video_path = Column(String(500))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Employee(id={self.id}, name={self.full_name}, code={self.employee_code})>"
