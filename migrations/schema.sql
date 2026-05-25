-- ============================================================
--  AlumniConnect – Upgraded MySQL Schema
--  Run: mysql -u root -p < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS alumni_mentorship
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE alumni_mentorship;

-- ── Users ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    name             VARCHAR(100) NOT NULL,
    email            VARCHAR(150) UNIQUE NOT NULL,
    password         VARCHAR(256) NOT NULL,
    role             ENUM('student','alumni','admin') DEFAULT 'student',
    is_active        BOOLEAN DEFAULT TRUE,
    email_verified   BOOLEAN DEFAULT FALSE,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role  (role)
);

-- ── Students ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS students (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL UNIQUE,
    department  VARCHAR(100),
    year        VARCHAR(10),
    skills      TEXT,
    interests   TEXT,
    bio         TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FULLTEXT idx_skills (skills, interests)
);

-- ── Alumni ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alumni (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL UNIQUE,
    graduation_year YEAR,
    company         VARCHAR(150),
    job_role        VARCHAR(150),
    skills          TEXT,
    location        VARCHAR(100),
    linkedin        VARCHAR(255),
    bio             TEXT,
    rating          DECIMAL(3,2) DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FULLTEXT idx_skills (skills, bio),
    INDEX idx_company (company),
    INDEX idx_job_role (job_role)
);

-- ── Mentorship Requests ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mentorship_requests (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    student_id  INT NOT NULL,
    alumni_id   INT NOT NULL,
    message     TEXT,
    status      ENUM('pending','accepted','rejected') DEFAULT 'pending',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (alumni_id)  REFERENCES alumni(id)   ON DELETE CASCADE,
    UNIQUE KEY uq_request (student_id, alumni_id),
    INDEX idx_alumni_id   (alumni_id),
    INDEX idx_student_id  (student_id),
    INDEX idx_status      (status)
);

-- ── Password Reset Tokens ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    token      VARCHAR(128) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used       BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
--  Seed Data (development only)
-- ============================================================

-- Admin user  (password: Admin@123)
INSERT IGNORE INTO users (name, email, password, role, is_active, email_verified) VALUES
('Admin', 'admin@college.edu',
 '$2b$12$K9pJN7lNfH4e5x6wD7q8Y.eJcT4v9uRK1HfPzYVoM2L3nX6qS0u3e',
 'admin', TRUE, TRUE);

-- Alumni (password: Pass@1234 – bcrypt; replace with generate_password_hash in real seed)
INSERT IGNORE INTO users (name, email, password, role, is_active, email_verified) VALUES
('Arjun Sharma',   'arjun@gmail.com',   '$2b$12$dummy_bcrypt_hash_placeholder', 'alumni', TRUE, TRUE),
('Priya Nair',     'priya@gmail.com',   '$2b$12$dummy_bcrypt_hash_placeholder', 'alumni', TRUE, TRUE),
('Vikram Rajan',   'vikram@gmail.com',  '$2b$12$dummy_bcrypt_hash_placeholder', 'alumni', TRUE, TRUE),
('Deepa Menon',    'deepa@gmail.com',   '$2b$12$dummy_bcrypt_hash_placeholder', 'alumni', TRUE, TRUE),
('Karthik Kumar',  'karthik@gmail.com', '$2b$12$dummy_bcrypt_hash_placeholder', 'alumni', TRUE, TRUE),
('Sneha Reddy',    'sneha@gmail.com',   '$2b$12$dummy_bcrypt_hash_placeholder', 'alumni', TRUE, TRUE),
('Rahul Verma',    'rahul@gmail.com',   '$2b$12$dummy_bcrypt_hash_placeholder', 'alumni', TRUE, TRUE),
('Divya Krishnan', 'divya@gmail.com',   '$2b$12$dummy_bcrypt_hash_placeholder', 'alumni', TRUE, TRUE);

-- NOTE: Run seed_users.py to generate correct bcrypt hashes for seed alumni/students.
