"""
SQL script to create database
Run this in MySQL before starting the application
"""

CREATE DATABASE IF NOT EXISTS face_recognition_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE face_recognition_db;

-- Employees table
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_code VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    department VARCHAR(100),
    position VARCHAR(100),
    embeddings TEXT NOT NULL,
    mean_embedding TEXT NOT NULL,
    image_paths TEXT,
    total_embeddings INT DEFAULT 0,
    registration_video_path VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_employee_code (employee_code),
    INDEX idx_full_name (full_name),
    INDEX idx_email (email),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Attendance logs table
CREATE TABLE IF NOT EXISTS attendance_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    employee_code VARCHAR(50) NOT NULL,
    employee_name VARCHAR(255) NOT NULL,
    confidence_score FLOAT NOT NULL,
    recognition_method VARCHAR(20),
    snapshot_path VARCHAR(500),
    location VARCHAR(255),
    check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    INDEX idx_employee_id (employee_id),
    INDEX idx_employee_code (employee_code),
    INDEX idx_check_in_time (check_in_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create user (optional, if needed)
-- CREATE USER 'face_recognition'@'localhost' IDENTIFIED BY 'your_password';
-- GRANT ALL PRIVILEGES ON face_recognition_db.* TO 'face_recognition'@'localhost';
-- FLUSH PRIVILEGES;
