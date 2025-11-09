"""
Employee Service for database operations
"""
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime
from loguru import logger

from app.models.employee import Employee
from app.models.schemas import EmployeeCreate, EmployeeUpdate
from app.services.face_recognition import face_service


class EmployeeService:
    """
    Service for employee CRUD operations
    """
    
    @staticmethod
    def create_employee(
        db: Session,
        employee_data: EmployeeCreate,
        embeddings: List,
        mean_embedding: List,
        image_paths: List[str] = None
    ) -> Employee:
        """
        Create new employee with face embeddings
        
        Args:
            db: Database session
            employee_data: Employee data
            embeddings: List of face embeddings
            mean_embedding: Mean embedding
            image_paths: List of image file paths
            
        Returns:
            Created Employee object
        """
        # Convert embeddings to JSON
        embeddings_json = json.dumps(embeddings)
        mean_embedding_json = json.dumps(mean_embedding)
        image_paths_json = json.dumps(image_paths) if image_paths else None
        
        # Create employee
        db_employee = Employee(
            employee_code=employee_data.employee_code,
            full_name=employee_data.full_name,
            email=employee_data.email,
            phone=employee_data.phone,
            department=employee_data.department,
            position=employee_data.position,
            embeddings=embeddings_json,
            mean_embedding=mean_embedding_json,
            image_paths=image_paths_json,
            total_embeddings=len(embeddings),
            is_active=True
        )
        
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
        
        logger.info(f"Created employee: {employee_data.employee_code} - {employee_data.full_name}")
        
        # Update face recognition service
        face_service.load_employee_db()
        
        return db_employee
    
    @staticmethod
    def get_employee(db: Session, employee_id: int) -> Optional[Employee]:
        """Get employee by ID"""
        return db.query(Employee).filter(Employee.id == employee_id).first()
    
    @staticmethod
    def get_employee_by_code(db: Session, employee_code: str) -> Optional[Employee]:
        """Get employee by employee code"""
        return db.query(Employee).filter(Employee.employee_code == employee_code).first()
    
    @staticmethod
    def get_employees(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Employee]:
        """Get list of employees"""
        query = db.query(Employee)
        
        if is_active is not None:
            query = query.filter(Employee.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def count_employees(db: Session, is_active: Optional[bool] = None) -> int:
        """Count total employees"""
        query = db.query(Employee)
        
        if is_active is not None:
            query = query.filter(Employee.is_active == is_active)
        
        return query.count()
    
    @staticmethod
    def update_employee(
        db: Session,
        employee_id: int,
        employee_update: EmployeeUpdate
    ) -> Optional[Employee]:
        """Update employee information"""
        db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
        
        if not db_employee:
            return None
        
        update_data = employee_update.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_employee, field, value)
        
        db_employee.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_employee)
        
        logger.info(f"Updated employee: {db_employee.employee_code}")
        
        return db_employee
    
    @staticmethod
    def delete_employee(db: Session, employee_id: int) -> bool:
        """Delete employee (soft delete - set is_active to False)"""
        db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
        
        if not db_employee:
            return False
        
        db_employee.is_active = False
        db_employee.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Deleted employee: {db_employee.employee_code}")
        
        # Reload face recognition database
        face_service.load_employee_db()
        
        return True
    
    @staticmethod
    def rebuild_face_db(db: Session):
        """
        Rebuild face recognition database from MySQL database
        """
        employees = db.query(Employee).filter(Employee.is_active == True).all()
        
        face_service.employee_db = {}
        
        for employee in employees:
            try:
                embeddings = json.loads(employee.embeddings)
                mean_embedding = json.loads(employee.mean_embedding)
                
                face_service.employee_db[employee.employee_code] = {
                    "all": embeddings,
                    "mean": mean_embedding
                }
            except Exception as e:
                logger.error(f"Error loading embeddings for {employee.employee_code}: {e}")
        
        face_service._save_employee_db()
        logger.info(f"Rebuilt face database: {len(face_service.employee_db)} employees")


employee_service = EmployeeService()
