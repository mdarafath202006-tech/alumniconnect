-- ============================================================
-- AlumniConnect – PostgreSQL (Supabase Compatible Schema)
-- ============================================================

-- USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(256) NOT NULL,
    role VARCHAR(20) DEFAULT 'student',
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- STUDENTS TABLE
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    department VARCHAR(100),
    year VARCHAR(10),
    skills TEXT,
    interests TEXT,
    bio TEXT,
    CONSTRAINT fk_students_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- ALUMNI TABLE
CREATE TABLE IF NOT EXISTS alumni (
    id SERIAL PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    graduation_year INT,
    company VARCHAR(150),
    job_role VARCHAR(150),
    skills TEXT,
    location VARCHAR(100),
    linkedin VARCHAR(255),
    bio TEXT,
    rating DECIMAL(3,2),

    CONSTRAINT fk_alumni_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_alumni_company ON alumni(company);
CREATE INDEX IF NOT EXISTS idx_alumni_job_role ON alumni(job_role);

-- MENTORSHIP REQUESTS
CREATE TABLE IF NOT EXISTS mentorship_requests (
    id SERIAL PRIMARY KEY,
    student_id INT NOT NULL,
    alumni_id INT NOT NULL,
    message TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_request_student
        FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_request_alumni
        FOREIGN KEY (alumni_id)
        REFERENCES alumni(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_request UNIQUE (student_id, alumni_id)
);

CREATE INDEX IF NOT EXISTS idx_request_alumni ON mentorship_requests(alumni_id);
CREATE INDEX IF NOT EXISTS idx_request_student ON mentorship_requests(student_id);
CREATE INDEX IF NOT EXISTS idx_request_status ON mentorship_requests(status);

-- PASSWORD RESET TOKENS
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(128) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_reset_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);