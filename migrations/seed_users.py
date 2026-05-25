"""
migrations/seed_users.py – Generate seed SQL with correct Werkzeug hashes.

Run ONCE:
  python migrations/seed_users.py | mysql -u root -p alumni_mentorship
"""
from werkzeug.security import generate_password_hash

alumni_seed = [
    (2, 2019, 'Google',    'Software Engineer',     'Python, Java, Machine Learning, Data Structures, Algorithms', 'Bangalore', 'Software engineer at Google with 5 years experience in ML and backend systems.'),
    (3, 2020, 'TCS',       'Data Analyst',          'Python, SQL, Tableau, Power BI, Statistics, Excel',           'Chennai',   'Data analyst helping businesses make data-driven decisions.'),
    (4, 2018, 'Infosys',   'Full Stack Developer',  'React, Node.js, MongoDB, JavaScript, CSS, HTML',              'Hyderabad', 'Full stack developer specialising in modern web applications.'),
    (5, 2021, 'Amazon',    'Cloud Architect',       'AWS, Docker, Kubernetes, Python, DevOps, Linux',              'Bangalore', 'Cloud architect designing scalable infrastructure on AWS.'),
    (6, 2017, 'Microsoft', 'AI Research Engineer',  'Deep Learning, TensorFlow, PyTorch, Python, NLP',             'Pune',      'AI researcher working on NLP and computer vision projects.'),
    (7, 2022, 'Wipro',     'Cybersecurity Analyst', 'Network Security, Ethical Hacking, Python, Kali Linux',       'Mumbai',    'Cybersecurity professional protecting enterprise systems.'),
    (8, 2019, 'Zoho',      'Product Manager',       'Product Management, Agile, Scrum, SQL, Communication',        'Chennai',   'Product manager driving user-centric product development.'),
    (9, 2020, 'Flipkart',  'Mobile App Developer',  'Flutter, Dart, Android, Kotlin, iOS, Swift, Firebase',        'Bangalore', 'Mobile developer building cross-platform applications.'),
]

student_seed = [
    (10, 'CSE', '3rd Year', 'Python, Machine Learning, SQL',  'Data Science, AI',      'Aspiring data scientist.'),
    (11, 'IT',  '2nd Year', 'HTML, CSS, JavaScript, React',   'Web Development',        'Frontend developer in making.'),
]

pw = generate_password_hash('Pass@1234')

print("-- ── Alumni profiles ────────────────────────────────────────────────")
for user_id, grad_yr, company, role, skills, loc, bio in alumni_seed:
    bio_esc = bio.replace("'", "\\'")
    skills_esc = skills.replace("'", "\\'")
    print(f"INSERT IGNORE INTO alumni (user_id, graduation_year, company, job_role, skills, location, bio) VALUES "
          f"({user_id}, {grad_yr}, '{company}', '{role}', '{skills_esc}', '{loc}', '{bio_esc}');")

print("\n-- ── Student profiles ───────────────────────────────────────────────")
for user_id, dept, year, skills, interests, bio in student_seed:
    print(f"INSERT IGNORE INTO students (user_id, department, year, skills, interests, bio) VALUES "
          f"({user_id}, '{dept}', '{year}', '{skills}', '{interests}', '{bio}');")

print(f"\n-- Password for all seed users: Pass@1234 (hash: {pw[:30]}…)")
