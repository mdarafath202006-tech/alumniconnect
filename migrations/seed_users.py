"""
Seed script for Supabase PostgreSQL (FINAL FIX)
Run: python migrations/seed_users.py
"""

import psycopg2
from werkzeug.security import generate_password_hash
import os


# ✅ Use single DATABASE_URL (BEST PRACTICE)
conn = psycopg2.connect(
    os.environ["DATABASE_URL"],
    sslmode="require"
)

cur = conn.cursor()

# ---------------- USERS ----------------
users = [
    ("Admin", "admin@college.edu", "Admin@123", "admin"),
]

alumni_users = [
    ("Arjun Sharma", "arjun@gmail.com", "Pass@1234", "alumni"),
    ("Priya Nair", "priya@gmail.com", "Pass@1234", "alumni"),
    ("Vikram Rajan", "vikram@gmail.com", "Pass@1234", "alumni"),
    ("Deepa Menon", "deepa@gmail.com", "Pass@1234", "alumni"),
    ("Karthik Kumar", "karthik@gmail.com", "Pass@1234", "alumni"),
    ("Sneha Reddy", "sneha@gmail.com", "Pass@1234", "alumni"),
    ("Rahul Verma", "rahul@gmail.com", "Pass@1234", "alumni"),
    ("Divya Krishnan", "divya@gmail.com", "Pass@1234", "alumni"),
]

student_users = [
    ("Student One", "student1@gmail.com", "Pass@1234", "student"),
    ("Student Two", "student2@gmail.com", "Pass@1234", "student"),
]

all_users = users + alumni_users + student_users

# ---------------- INSERT USERS ----------------
user_ids = []

for name, email, password, role in all_users:
    hashed_pw = generate_password_hash(password)

    cur.execute("""
        INSERT INTO users (name, email, password, role)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (name, email, hashed_pw, role))

    user_id = cur.fetchone()[0]
    user_ids.append((user_id, role))

print("Users inserted successfully!")

# ---------------- ALUMNI ----------------
alumni_seed = [
    (user_ids[1][0], 2019, 'Google', 'Software Engineer',
     'Python, Java, ML, DS', 'Bangalore',
     'Software engineer at Google'),

    (user_ids[2][0], 2020, 'TCS', 'Data Analyst',
     'Python, SQL, Tableau', 'Chennai',
     'Data analyst at TCS'),
]

for user_id, grad_yr, company, role, skills, loc, bio in alumni_seed:
    cur.execute("""
        INSERT INTO alumni
        (user_id, graduation_year, company, job_role, skills, location, bio)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (user_id, grad_yr, company, role, skills, loc, bio))

# ---------------- STUDENTS ----------------
student_seed = [
    (user_ids[-2][0], 'CSE', '3rd Year',
     'Python, ML, SQL', 'AI, Data Science',
     'Aspiring data scientist'),

    (user_ids[-1][0], 'IT', '2nd Year',
     'HTML, CSS, JS', 'Web Dev',
     'Frontend developer in making'),
]

for user_id, dept, year, skills, interests, bio in student_seed:
    cur.execute("""
        INSERT INTO students
        (user_id, department, year, skills, interests, bio)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (user_id, dept, year, skills, interests, bio))

conn.commit()
cur.close()
conn.close()

print("🎉 Seeding completed successfully!")
