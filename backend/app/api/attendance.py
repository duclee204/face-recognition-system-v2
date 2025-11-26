"""
Attendance API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from loguru import logger

from app.core.database import get_db
from app.models.schemas import (
    AttendanceLogResponse, AttendanceListResponse, AttendanceStatsResponse
)
from app.services.attendance import attendance_service

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.get("/logs", response_model=AttendanceListResponse)
async def get_attendance_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    employee_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get attendance logs with filters
    
    Query parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    - employee_id: Filter by employee ID
    - start_date: Filter from this date (ISO format)
    - end_date: Filter until this date (ISO format)
    """
    try:
        # Parse dates if provided
        start_datetime = None
        end_datetime = None
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                )
        
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                )
        
        # Get logs
        logs = attendance_service.get_attendance_logs(
            db=db,
            skip=skip,
            limit=limit,
            employee_id=employee_id,
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        total = attendance_service.count_attendance_logs(
            db=db,
            employee_id=employee_id,
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        return AttendanceListResponse(
            total=total,
            logs=logs
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting attendance logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/today")
async def get_today_attendance(
    db: Session = Depends(get_db)
):
    """Get today's attendance logs"""
    try:
        logs = attendance_service.get_today_attendance(db)
        
        return {
            "success": True,
            "date": datetime.now().date().isoformat(),
            "total": len(logs),
            "logs": logs
        }
        
    except Exception as e:
        logger.error(f"Error getting today's attendance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/stats", response_model=AttendanceStatsResponse)
async def get_attendance_stats(
    db: Session = Depends(get_db)
):
    """
    Get attendance statistics
    
    Returns statistics for:
    - Today
    - This week
    - This month
    - Unique employees today
    """
    try:
        stats = attendance_service.get_attendance_stats(db)
        return AttendanceStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting attendance stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/employee/{employee_id}")
async def get_employee_attendance(
    employee_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get attendance logs for specific employee
    """
    try:
        # Parse dates if provided
        start_datetime = None
        end_datetime = None
        
        if start_date:
            start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        if end_date:
            end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        logs = attendance_service.get_attendance_logs(
            db=db,
            skip=skip,
            limit=limit,
            employee_id=employee_id,
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        total = attendance_service.count_attendance_logs(
            db=db,
            employee_id=employee_id,
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        return {
            "success": True,
            "employee_id": employee_id,
            "total": total,
            "logs": logs
        }
        
    except Exception as e:
        logger.error(f"Error getting employee attendance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/check-in-status/{employee_id}")
async def check_in_status(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Check employee attendance status for today
    Returns: not-checked-in or checked-in (check-out updates continuously)
    """
    try:
        status_today = attendance_service.get_attendance_status_today(db, employee_id)
        has_checked_in = attendance_service.has_checked_in_today(db, employee_id)
        
        # Get today's attendance record to show check-out time
        from datetime import date
        today = date.today()
        attendance = db.query(attendance_service.__class__.__module__).first()  # Get AttendanceLog
        from app.models.attendance import AttendanceLog
        attendance_record = db.query(AttendanceLog).filter(
            AttendanceLog.employee_id == employee_id,
            AttendanceLog.work_date == today
        ).first()
        
        response = {
            "success": True,
            "employee_id": employee_id,
            "status": status_today,
            "has_checked_in_today": has_checked_in,
            "date": today.isoformat(),
            "message": {
                "not-checked-in": "Employee has not checked in yet",
                "checked-in": "Employee is checked in (check-out updates automatically)"
            }[status_today]
        }
        
        if attendance_record:
            response["check_in"] = attendance_record.check_in.isoformat() if attendance_record.check_in else None
            response["check_out"] = attendance_record.check_out.isoformat() if attendance_record.check_out else None
            response["total_hours"] = float(attendance_record.total_hours) if attendance_record.total_hours else None
        
        return response
        
    except Exception as e:
        logger.error(f"Error checking in status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
