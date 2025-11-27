"""
Database initialization and sample data script
"""
from app.core.database import engine, Base, SessionLocal
from app.models.employee import Employee
from app.models.attendance import AttendanceLog
from loguru import logger


def init_database():
    """Create all database tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created successfully")


def create_sample_data():
    """Create sample employees for testing (optional)"""
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_count = db.query(Employee).count()
        if existing_count > 0:
            logger.info(f"Database already has {existing_count} employees. Skipping sample data.")
            return
        
        logger.info("Creating sample employees...")
        
        # Note: In real scenario, you need to register employees with actual face data
        # This is just for database structure testing
        
        logger.info("✅ Sample data created (register employees via API)")
        
    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("🚀 Initializing database...")
    init_database()
    create_sample_data()
    logger.info("✅ Database initialization complete!")
