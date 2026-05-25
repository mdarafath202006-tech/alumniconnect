"""
app/ai/recommender.py – Advanced multi-factor mentor recommendation engine.

Upgrades over original TF-IDF-only approach:
  ✅ TF-IDF cosine similarity (skills & bio)
  ✅ Exact skill-keyword overlap bonus
  ✅ Industry / department alignment bonus
  ✅ Weighted composite score with configurable weights
  ✅ Career analytics (unchanged API surface)
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import re


# ── Configurable weights ──────────────────────────────────────────────────────
WEIGHTS = {
    "tfidf":    0.55,   # semantic similarity
    "skill":    0.30,   # exact skill keyword overlap
    "industry": 0.15,   # dept / industry match
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def _tokenize_skills(text: str) -> set:
    """Split comma/semicolon/pipe separated skills into a lowercase set."""
    if not text:
        return set()
    return {s.strip().lower() for s in re.split(r"[,;|]+", text) if s.strip()}


def _build_text(record: dict, fields: list) -> str:
    return " ".join(str(record.get(f) or "").lower().strip() for f in fields)


def _skill_overlap_score(student: dict, alumnus: dict) -> float:
    """Jaccard-like skill overlap in [0, 1]."""
    s_skills = _tokenize_skills(student.get("skills", "")) | \
               _tokenize_skills(student.get("interests", ""))
    a_skills = _tokenize_skills(alumnus.get("skills", ""))
    if not s_skills or not a_skills:
        return 0.0
    intersection = s_skills & a_skills
    union = s_skills | a_skills
    return len(intersection) / len(union)


def _industry_score(student: dict, alumnus: dict) -> float:
    """Rough industry/department alignment."""
    dept = (student.get("department") or "").lower()
    role = (alumnus.get("job_role") or "").lower()
    bio  = (alumnus.get("bio") or "").lower()
    # CS/IT students → tech alumni
    cs_keywords = {"cse", "cs", "computer", "it", "software", "data", "ai", "ml"}
    if dept and any(k in dept for k in cs_keywords):
        tech_keywords = {"software", "data", "ai", "ml", "engineer", "developer", "analyst", "cloud"}
        if any(k in role or k in bio for k in tech_keywords):
            return 1.0
    # Generic department word present in role?
    if dept and dept.split()[0] in role:
        return 0.6
    return 0.0


# ── Public API ────────────────────────────────────────────────────────────────
def get_recommendations(student: dict, alumni_list: list, top_n: int = 10) -> list:
    """
    Return top_n alumni ranked by composite score.

    Each result: {"alumni": {...}, "score": float, "percent": int,
                  "skill_overlap": int, "matched_skills": list}
    """
    if not alumni_list:
        return []

    student_text = _build_text(student, ["skills", "interests", "department"])
    alumni_texts = [_build_text(a, ["skills", "job_role", "company", "bio"]) for a in alumni_list]

    # ── TF-IDF similarity ─────────────────────────────────────────────────────
    all_texts = [student_text] + alumni_texts
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
    try:
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        tfidf_scores = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1:]).flatten()
    except ValueError:
        tfidf_scores = [0.0] * len(alumni_list)

    # ── Composite scoring ─────────────────────────────────────────────────────
    results = []
    s_skills = _tokenize_skills(student.get("skills", "")) | \
               _tokenize_skills(student.get("interests", ""))

    for i, alumnus in enumerate(alumni_list):
        tfidf_s  = float(tfidf_scores[i])
        skill_s  = _skill_overlap_score(student, alumnus)
        ind_s    = _industry_score(student, alumnus)

        composite = (
            WEIGHTS["tfidf"]    * tfidf_s +
            WEIGHTS["skill"]    * skill_s +
            WEIGHTS["industry"] * ind_s
        )

        a_skills     = _tokenize_skills(alumnus.get("skills", ""))
        matched      = sorted(s_skills & a_skills)

        results.append({
            "alumni":         alumnus,
            "score":          round(composite, 4),
            "percent":        min(int(composite * 100), 99),
            "skill_overlap":  int(skill_s * 100),
            "matched_skills": matched,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]


def get_career_analytics(alumni_data: list) -> dict:
    """Generate career analytics from alumni records."""
    companies, roles, skills_all, years = [], [], [], []

    for a in alumni_data:
        if a.get("company"):
            companies.append(a["company"].strip().title())
        if a.get("job_role"):
            roles.append(a["job_role"].strip().title())
        if a.get("skills"):
            for sk in re.split(r"[,;|]+", a["skills"]):
                sk = sk.strip().title()
                if sk:
                    skills_all.append(sk)
        if a.get("graduation_year"):
            years.append(str(a["graduation_year"]))

    def top(lst, n=8):
        return [{"label": k, "count": v} for k, v in Counter(lst).most_common(n)]

    return {
        "top_companies": top(companies),
        "top_roles":     top(roles),
        "top_skills":    top(skills_all, 12),
        "by_year":       top(years, 10),
    }


def get_skill_gap(student: dict, target_role: str, alumni_list: list) -> dict:
    """
    Compare student skills against alumni in the target role.
    Returns: {required_skills, student_has, missing, coverage_pct}
    """
    target = target_role.lower()
    relevant = [
        a for a in alumni_list
        if target in (a.get("job_role") or "").lower()
    ]
    if not relevant:
        return {"required_skills": [], "student_has": [], "missing": [], "coverage_pct": 0}

    role_skills = Counter()
    for a in relevant:
        for sk in _tokenize_skills(a.get("skills", "")):
            role_skills[sk] += 1

    # skills appearing in >30 % of role holders
    threshold = max(1, len(relevant) * 0.3)
    required  = {sk for sk, cnt in role_skills.items() if cnt >= threshold}
    s_skills  = _tokenize_skills(student.get("skills", "")) | \
                _tokenize_skills(student.get("interests", ""))

    has     = sorted(required & s_skills)
    missing = sorted(required - s_skills)
    pct     = int(len(has) / len(required) * 100) if required else 100

    return {
        "required_skills": sorted(required),
        "student_has":     has,
        "missing":         missing,
        "coverage_pct":    pct,
    }
