"""
Attendance Service for logging and querying attendance records
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, timedelta
from loguru import logger

from app.models.attendance import AttendanceLog
from app.models.employee import Employee


class AttendanceService:
    """
    Service for attendance logging and statistics
    """
    
    @staticmethod
    def log_attendance(
        db: Session,
        employee_id: int,
        employee_code: str,
        employee_name: str,
        confidence_score: float,
        recognition_method: str,
        snapshot_path: Optional[str] = None,
        location: Optional[str] = None
    ) -> AttendanceLog:
        """
        Log attendance record
        
        Args:
            db: Database session
            employee_id: Employee ID
            employee_code: Employee code
            employee_name: Employee name
            confidence_score: Recognition confidence
            recognition_method: Recognition method used
            snapshot_path: Path to snapshot image
            location: Check-in location
            
        Returns:
            Created AttendanceLog object
        """
        attendance = AttendanceLog(
            employee_id=employee_id,
            employee_code=employee_code,
            employee_name=employee_name,
            confidence_score=confidence_score,
            recognition_method=recognition_method,
            snapshot_path=snapshot_path,
            location=location
        )
        
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        
        logger.info(f"✅ Attendance logged: {employee_name} ({confidence_score:.3f})")
        
        return attendance
    
    @staticmethod
    def get_attendance_logs(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        employee_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AttendanceLog]:
        """
        Get attendance logs with filters
        
        Args:
            db: Database session
            skip: Offset
            limit: Limit
            employee_id: Filter by employee ID
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            List of AttendanceLog objects
        """
        query = db.query(AttendanceLog)
        
        if employee_id:
            query = query.filter(AttendanceLog.employee_id == employee_id)
        
        if start_date:
            query = query.filter(AttendanceLog.check_in_time >= start_date)
        
        if end_date:
            query = query.filter(AttendanceLog.check_in_time <= end_date)
        
        return query.order_by(AttendanceLog.check_in_time.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def count_attendance_logs(
        db: Session,
        employee_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Count attendance logs with filters"""
        query = db.query(AttendanceLog)
        
        if employee_id:
            query = query.filter(AttendanceLog.employee_id == employee_id)
        
        if start_date:
            query = query.filter(AttendanceLog.check_in_time >= start_date)
        
        if end_date:
            query = query.filter(AttendanceLog.check_in_time <= end_date)
        
        return query.count()
    
    @staticmethod
    def get_today_attendance(db: Session) -> List[AttendanceLog]:
        """Get today's attendance logs"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        return db.query(AttendanceLog).filter(
            and_(
                AttendanceLog.check_in_time >= today,
                AttendanceLog.check_in_time < tomorrow
            )
        ).order_by(AttendanceLog.check_in_time.desc()).all()
    
    @staticmethod
    def get_attendance_stats(db: Session) -> dict:
        """
        Get attendance statistics
        
        Returns:
            Dictionary with statistics
        """
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        # Today's stats
        total_today = db.query(AttendanceLog).filter(
            AttendanceLog.check_in_time >= today
        ).count()
        
        unique_today = db.query(func.count(func.distinct(AttendanceLog.employee_id))).filter(
            AttendanceLog.check_in_time >= today
        ).scalar()
        
        # This week
        total_week = db.query(AttendanceLog).filter(
            AttendanceLog.check_in_time >= week_start
        ).count()
        
        # This month
        total_month = db.query(AttendanceLog).filter(
            AttendanceLog.check_in_time >= month_start
        ).count()
        
        return {
            "total_today": total_today,
            "total_this_week": total_week,
            "total_this_month": total_month,
            "unique_employees_today": unique_today or 0
        }
    
    @staticmethod
    def has_checked_in_today(db: Session, employee_id: int) -> bool:
        """
        Check if employee has already checked in today
        
        Args:
            db: Database session
            employee_id: Employee ID
            
        Returns:
            True if already checked in
        """
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        count = db.query(AttendanceLog).filter(
            and_(
                AttendanceLog.employee_id == employee_id,
                AttendanceLog.check_in_time >= today
            )
        ).count()
        
        return count > 0


attendance_service = AttendanceService()
