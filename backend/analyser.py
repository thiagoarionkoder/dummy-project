"""The actual science. Do not question it."""

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

VERDICTS = [
    (95, "HIRE IMMEDIATELY", "Print this CV. Frame it. Give them the corner desk."),
    (80, "STRONG YES", "Suspiciously competent. Check the references anyway."),
    (65, "PROBABLY FINE", "Would survive a code review. Mostly."),
    (50, "HMMM", "The CV equivalent of lukewarm coffee."),
    (35, "NEEDS SEASONING", "Add verbs. Remove adjectives. Try again."),
    (0,  "BOLD CHOICE", "This CV was written at 3am and it shows."),
]


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
            "score": 0,
            "verdict": "EMPTY",
            "roast": "You submitted nothing. Bold. Minimalist. Unemployed.",
            "stats": {"words": 0, "buzzwords": 0, "skills": 0,
                      "years_claimed": 0, "exclamations": 0,
                      "coffee_index": 0, "reading_time_s": 0},
            "found_skills": [],
            "found_buzzwords": [],
            "notes": ["Try pasting an actual curriculum. Any curriculum."],
        }

    found_buzzwords = sorted({b for b in BUZZWORDS if b in lower})
    found_skills = sorted({s for s in SKILLS if re.search(rf"(?<![a-z]){re.escape(s)}(?![a-z])", lower)})

    years = [int(y) for y in re.findall(r"(\d{1,2})\+?\s*(?:years?|yrs?)", lower)]
    years_claimed = sum(years)

    exclamations = text.count("!")
    unique_ratio = len({w.lower() for w in words}) / word_count

    # Peer-reviewed formula (peer = me).
    score = 40
    score += min(len(found_skills) * 5, 30)
    score += min(word_count // 40, 12)
    score += int(unique_ratio * 20)
    score -= min(len(found_buzzwords) * 6, 30)
    score -= min(exclamations * 3, 15)
    score -= 8 if years_claimed > 40 else 0
    score += _stable_noise(text, "vibes", 11) - 5  # the vibes coefficient
    score = max(0, min(100, score))

    verdict, roast = "SUMMARY", "Here is what the CV contains. No score, no ranking."

    notes = []
    if found_buzzwords:
        notes.append(f"Detected {len(found_buzzwords)} buzzword(s). The corporate is coming from inside the house.")
    if exclamations > 3:
        notes.append(f"{exclamations} exclamation marks. Calm down.")
    if years_claimed > 40:
        notes.append(f"You claim {years_claimed} total years of experience. Are you a vampire?")
    if years_claimed and years_claimed <= 40:
        notes.append(f"Roughly {years_claimed} years claimed across all roles. Noted, believed, not verified.")
    if not found_skills:
        notes.append("No recognisable hard skills found. Vibes-based candidate.")
    for skill, comment in CURSED_SKILLS.items():
        if skill in found_skills:
            notes.append(comment)
    if unique_ratio < 0.4:
        notes.append("Extremely repetitive. Did you copy-paste a role five times?")
    if not notes:
        notes.append("Nothing alarming. Genuinely unsettling.")

    return {
        "verdict": verdict,
        "roast": roast,
        "stats": {
            "words": word_count,
            "buzzwords": len(found_buzzwords),
            "skills": len(found_skills),
            "years_claimed": years_claimed,
            "exclamations": exclamations,
            "coffee_index": round(1.5 + _stable_noise(text, "coffee", 60) / 10, 1),
            "reading_time_s": max(5, round(word_count / 3.5)),
        },
        "found_skills": found_skills,
        "found_buzzwords": found_buzzwords,
        "notes": notes,
    }
