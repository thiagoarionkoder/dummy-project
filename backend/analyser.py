"""Extraction only.

The automated scoring and ranking of candidates was removed. This module now
only surfaces the fields it found in the text so a recruiter can read them; it
produces no score, no ranking, and no evaluation of any individual.
"""

import hashlib
import re

BUZZWORDS = [
    "synergy", "leverage", "disrupt", "rockstar", "ninja", "guru",
    "10x", "paradigm", "holistic", "proactive", "ecosystem",
    "thought leader", "dynamic", "passionate", "detail-oriented",
    "team player", "self-starter", "results-driven", "outside the box",
]

SKILLS = [
    "python", "javascript", "typescript", "java", "go", "rust", "c++",
    "sql", "react", "vue", "angular", "node", "django", "flask",
    "docker", "kubernetes", "aws", "azure", "gcp", "terraform",
    "excel", "powerpoint", "photoshop", "figma", "git",
]

# Skills that are, frankly, a red flag.
CURSED_SKILLS = {"powerpoint": "Nobody puts PowerPoint on a CV voluntarily.",
                 "excel": "Excel is a database now, apparently.",
                 "c++": "Respect. Also: are you okay?"}


def _stable_noise(text: str, salt: str, span: int) -> int:
    """Deterministic fake randomness, so refreshing doesn't change the verdict."""
    digest = hashlib.sha256((salt + text).encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % span


def analyse(text: str) -> dict:
    text = (text or "").strip()
    lower = text.lower()
    words = re.findall(r"[A-Za-z'+#]+", text)
    word_count = len(words)

    if word_count == 0:
        return {
            "stats": {"words": 0, "buzzwords": 0, "skills": 0,
                      "years_claimed": 0, "reading_time_s": 0},
            "found_skills": [],
            "found_buzzwords": [],
            "notes": ["Nothing submitted. Nothing extracted."],
        }

    found_buzzwords = sorted({b for b in BUZZWORDS if b in lower})
    found_skills = sorted({s for s in SKILLS if re.search(rf"(?<![a-z]){re.escape(s)}(?![a-z])", lower)})

    years = [int(y) for y in re.findall(r"(\d{1,2})\+?\s*(?:years?|yrs?)", lower)]
    years_claimed = sum(years)

    notes = []
    for skill, comment in CURSED_SKILLS.items():
        if skill in found_skills:
            notes.append(comment)
    if not notes:
        notes.append("Extracted fields only. No evaluation performed.")

    # No score, no verdict, no ranking: a recruiter reads these fields and
    # decides. Nothing here evaluates or ranks a person.
    return {
        "stats": {
            "words": word_count,
            "buzzwords": len(found_buzzwords),
            "skills": len(found_skills),
            "years_claimed": years_claimed,
            "reading_time_s": max(5, round(word_count / 3.5)),
        },
        "found_skills": found_skills,
        "found_buzzwords": found_buzzwords,
        "notes": notes,
    }
