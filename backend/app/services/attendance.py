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
        camera_id: Optional[int] = None
    ) -> tuple[AttendanceLog, str]:
        """
        Log attendance record - automatically handles check-in or check-out
        Logic: 
        - First recognition of the day = check-in
        - All subsequent recognitions = update check-out (continuously updated)
        
        Args:
            db: Database session
            employee_id: Employee ID
            camera_id: Camera ID used for recognition
            
        Returns:
            Tuple of (AttendanceLog object, action: 'check-in' or 'check-out')
        """
        today = datetime.now().date()
        now = datetime.now()
        
        # Check if already has attendance record for today
        existing = db.query(AttendanceLog).filter(
            and_(
                AttendanceLog.employee_id == employee_id,
                AttendanceLog.work_date == today
            )
        ).first()
        
        if not existing:
            # First time today - CREATE new record with check-in
            attendance = AttendanceLog(
                employee_id=employee_id,
                camera_id=camera_id,
                work_date=today,
                check_in=now,
                status="checked-in"
            )
            
            db.add(attendance)
            db.commit()
            db.refresh(attendance)
            
            logger.info(f"✅ CHECK-IN: employee_id {employee_id} at {now.strftime('%H:%M:%S')}")
            return attendance, "check-in"
            
        else:
            # Has check-in - ALWAYS UPDATE check-out (continuous update)
            existing.check_out = now
            
            # Calculate total hours
            time_diff = existing.check_out - existing.check_in
            existing.total_hours = round(time_diff.total_seconds() / 3600, 2)
            existing.status = "completed"
            
            db.commit()
            db.refresh(existing)
            
            logger.info(f"🔄 CHECK-OUT UPDATED: employee_id {employee_id} at {now.strftime('%H:%M:%S')} (Total: {existing.total_hours}h)")
            return existing, "check-out"
    
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
            query = query.filter(AttendanceLog.check_in >= start_date)
        
        if end_date:
            query = query.filter(AttendanceLog.check_in <= end_date)
        
        return query.order_by(AttendanceLog.check_in.desc()).offset(skip).limit(limit).all()
    
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
            query = query.filter(AttendanceLog.check_in >= start_date)
        
        if end_date:
            query = query.filter(AttendanceLog.check_in <= end_date)
        
        return query.count()
    
    @staticmethod
    def get_today_attendance(db: Session) -> List[AttendanceLog]:
        """Get today's attendance logs"""
        today = datetime.now().date()
        
        return db.query(AttendanceLog).filter(
            AttendanceLog.work_date == today
        ).order_by(AttendanceLog.check_in.desc()).all()
    
    @staticmethod
    def get_attendance_stats(db: Session) -> dict:
        """
        Get attendance statistics
        
        Returns:
            Dictionary with statistics
        """
        now = datetime.now()
        today = now.date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        # Today's stats
        total_today = db.query(AttendanceLog).filter(
            AttendanceLog.work_date == today
        ).count()
        
        unique_today = db.query(func.count(func.distinct(AttendanceLog.employee_id))).filter(
            AttendanceLog.work_date == today
        ).scalar()
        
        # This week
        total_week = db.query(AttendanceLog).filter(
            AttendanceLog.work_date >= week_start
        ).count()
        
        # This month
        total_month = db.query(AttendanceLog).filter(
            AttendanceLog.work_date >= month_start
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
        today = datetime.now().date()
        
        attendance = db.query(AttendanceLog).filter(
            and_(
                AttendanceLog.employee_id == employee_id,
                AttendanceLog.work_date == today
            )
        ).first()
        
        return attendance is not None and attendance.check_in is not None
    
    @staticmethod
    def get_attendance_status_today(db: Session, employee_id: int) -> str:
        """
        Get attendance status for today
        
        Args:
            db: Database session
            employee_id: Employee ID
            
        Returns:
            'not-checked-in' or 'checked-in' (with continuous check-out updates)
        """
        today = datetime.now().date()
        
        attendance = db.query(AttendanceLog).filter(
            and_(
                AttendanceLog.employee_id == employee_id,
                AttendanceLog.work_date == today
            )
        ).first()
        
        if not attendance or not attendance.check_in:
            return "not-checked-in"
        else:
            return "checked-in"  # Always "checked-in" after first recognition


attendance_service = AttendanceService()
