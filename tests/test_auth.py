"""
tests/test_auth.py – Unit tests for auth and AI modules.

Run:
  pytest tests/ -v
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ── AI module tests (no DB required) ─────────────────────────────────────────
from app.ai.recommender import (
    get_recommendations, get_career_analytics, get_skill_gap,
    _tokenize_skills, _skill_overlap_score, _industry_score,
)
from app.utils.validators import validate_email, validate_password, sanitize


class TestTokenizer:
    def test_comma_separated(self):
        assert _tokenize_skills("Python, SQL, React") == {"python", "sql", "react"}

    def test_pipe_separated(self):
        assert _tokenize_skills("Python|SQL|React") == {"python", "sql", "react"}

    def test_empty(self):
        assert _tokenize_skills("") == set()

    def test_none(self):
        assert _tokenize_skills(None) == set()


class TestSkillOverlap:
    def test_full_overlap(self):
        s = {"skills": "Python, SQL"}
        a = {"skills": "Python, SQL"}
        assert _skill_overlap_score(s, a) == 1.0

    def test_no_overlap(self):
        s = {"skills": "React"}
        a = {"skills": "Java"}
        assert _skill_overlap_score(s, a) == 0.0

    def test_partial(self):
        s = {"skills": "Python, SQL, React"}
        a = {"skills": "Python, Java"}
        score = _skill_overlap_score(s, a)
        assert 0 < score < 1


class TestRecommendations:
    ALUMNI = [
        {"id": 1, "name": "A1", "skills": "Python, Machine Learning", "job_role": "Data Scientist",
         "company": "Google", "bio": "ML expert", "location": "Bangalore", "email": "a1@g.com"},
        {"id": 2, "name": "A2", "skills": "React, Node.js, JavaScript", "job_role": "Frontend Dev",
         "company": "TCS", "bio": "Web dev", "location": "Chennai", "email": "a2@g.com"},
    ]

    def test_returns_list(self):
        student = {"skills": "Python, SQL", "interests": "AI", "department": "CSE"}
        result = get_recommendations(student, self.ALUMNI)
        assert isinstance(result, list)

    def test_correct_structure(self):
        student = {"skills": "Python", "interests": "ML", "department": "CSE"}
        result = get_recommendations(student, self.ALUMNI, top_n=2)
        for item in result:
            assert "alumni" in item
            assert "score" in item
            assert "percent" in item
            assert "matched_skills" in item

    def test_empty_alumni(self):
        student = {"skills": "Python", "interests": "ML", "department": "CSE"}
        assert get_recommendations(student, []) == []

    def test_relevant_alumni_ranked_first(self):
        student = {"skills": "Python, Machine Learning", "interests": "AI", "department": "CSE"}
        result = get_recommendations(student, self.ALUMNI)
        assert result[0]["alumni"]["id"] == 1  # ML alumni should rank first

    def test_top_n_respected(self):
        student = {"skills": "Python", "interests": "ML", "department": "CSE"}
        result = get_recommendations(student, self.ALUMNI, top_n=1)
        assert len(result) == 1


class TestCareerAnalytics:
    DATA = [
        {"job_role": "Software Engineer", "company": "Google",  "skills": "Python, Java", "graduation_year": 2020},
        {"job_role": "Data Analyst",      "company": "TCS",     "skills": "Python, SQL",  "graduation_year": 2021},
        {"job_role": "Software Engineer", "company": "Google",  "skills": "Java, Spring", "graduation_year": 2020},
    ]

    def test_returns_dict(self):
        result = get_career_analytics(self.DATA)
        assert isinstance(result, dict)
        assert "top_companies" in result
        assert "top_roles" in result
        assert "top_skills" in result
        assert "by_year" in result

    def test_top_company_correct(self):
        result = get_career_analytics(self.DATA)
        assert result["top_companies"][0]["label"] == "Google"
        assert result["top_companies"][0]["count"] == 2

    def test_empty(self):
        result = get_career_analytics([])
        assert result["top_companies"] == []


class TestSkillGap:
    ALUMNI = [
        {"skills": "Python, SQL, Pandas, Machine Learning", "job_role": "Data Scientist"},
        {"skills": "Python, SQL, Pandas, Statistics", "job_role": "Data Scientist"},
    ]

    def test_has_some_missing(self):
        student = {"skills": "Python, SQL", "interests": "Data"}
        result = get_skill_gap(student, "Data Scientist", self.ALUMNI)
        assert "required_skills" in result
        assert "student_has" in result
        assert "missing" in result
        assert "coverage_pct" in result
        assert "python" in result["student_has"]

    def test_no_matching_role(self):
        student = {"skills": "Python", "interests": "AI"}
        result = get_skill_gap(student, "Astronaut", self.ALUMNI)
        assert result["coverage_pct"] == 0


class TestValidators:
    def test_valid_email(self):
        assert validate_email("user@example.com") is True

    def test_invalid_email(self):
        assert validate_email("notanemail") is False

    def test_strong_password(self):
        ok, _ = validate_password("StrongPass1")
        assert ok is True

    def test_weak_password_short(self):
        ok, msg = validate_password("abc")
        assert ok is False
        assert "8" in msg

    def test_weak_password_no_upper(self):
        ok, msg = validate_password("weakpass1")
        assert ok is False

    def test_sanitize_strips(self):
        assert sanitize("  hello  ") == "hello"

    def test_sanitize_truncates(self):
        assert len(sanitize("x" * 1000, max_len=10)) == 10
