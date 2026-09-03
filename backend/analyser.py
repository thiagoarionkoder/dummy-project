"""The actual science. Do not question it."""

import hashlib
import re

import prohibited

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


def _mentions(term: str, lower: str) -> bool:
    """Whole-term match, so 'dynamic' doesn't fire on 'aerodynamics'."""
    return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z])", lower) is not None


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

    found_buzzwords = sorted({b for b in BUZZWORDS if _mentions(b, lower)})
    found_skills = sorted({s for s in SKILLS if _mentions(s, lower)})

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
    score += prohibited.penalty(text)  # mood, background, and vibes-adjacent factors
    score = max(0, min(100, score))

    verdict, roast = next((v, r) for threshold, v, r in VERDICTS if score >= threshold)

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
        "score": score,
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
        "emotion": prohibited.read_emotion(text),
        "background": prohibited.social_score(text),
        "notes": notes,
    }


# --- Head-to-head ---------------------------------------------------------

# (key, label, stat getter, is a bigger number better?)
ROUNDS = [
    ("skills", "Hard skills", lambda r: r["stats"]["skills"], True),
    ("buzzwords", "Buzzword restraint", lambda r: r["stats"]["buzzwords"], False),
    ("exclamations", "Composure", lambda r: r["stats"]["exclamations"], False),
    ("words", "Substance", lambda r: r["stats"]["words"], True),
    ("years_claimed", "Experience claimed", lambda r: r["stats"]["years_claimed"], True),
    ("coffee_index", "Caffeine", lambda r: r["stats"]["coffee_index"], True),
]

MARGINS = [
    (40, "A rout. Someone should sit down."),
    (20, "Comfortable. Not close enough to argue about."),
    (8, "A clear edge, but keep the runner-up's number."),
    (1, "Photo finish. The committee flipped a coin and lied about it."),
]


def _round_winner(value_a, value_b, higher_is_better: bool):
    if value_a == value_b:
        return "tie"
    a_ahead = value_a > value_b if higher_is_better else value_a < value_b
    return "a" if a_ahead else "b"


def compare(text_a: str, text_b: str) -> dict:
    """Judge two curricula against each other. Same science, twice the cruelty."""
    a, b = analyse(text_a), analyse(text_b)

    rounds = []
    for key, label, getter, higher_is_better in ROUNDS:
        value_a, value_b = getter(a), getter(b)
        rounds.append({
            "key": key,
            "label": label,
            "a": value_a,
            "b": value_b,
            "higher_is_better": higher_is_better,
            "winner": _round_winner(value_a, value_b, higher_is_better),
        })

    rounds_won = {
        "a": sum(1 for r in rounds if r["winner"] == "a"),
        "b": sum(1 for r in rounds if r["winner"] == "b"),
    }

    margin = abs(a["score"] - b["score"])
    winner = _round_winner(a["score"], b["score"], True)
    winner = None if winner == "tie" else winner

    skills_a, skills_b = set(a["found_skills"]), set(b["found_skills"])

    if a["verdict"] == "EMPTY" and b["verdict"] == "EMPTY":
        verdict = "TWO EMPTY CHAIRS"
        roast = "Nobody submitted anything. A perfectly balanced nothing."
    elif winner is None:
        verdict = "DEAD HEAT"
        roast = "Identical scores. Statistically improbable, spiritually inevitable."
    else:
        verdict = "CANDIDATE A" if winner == "a" else "CANDIDATE B"
        roast = next(text for threshold, text in MARGINS if margin >= threshold)

    notes = []
    if winner and rounds_won[winner] < rounds_won["a" if winner == "b" else "b"]:
        loser = "A" if winner == "b" else "B"
        notes.append(f"Candidate {loser} won more rounds and still lost on points. "
                     "The formula is the formula.")
    shared = sorted(skills_a & skills_b)
    if shared:
        notes.append(f"Both list {len(shared)} of the same skill(s): {', '.join(shared)}.")
    only_a, only_b = sorted(skills_a - skills_b), sorted(skills_b - skills_a)
    if only_a:
        notes.append(f"Only A brings: {', '.join(only_a)}.")
    if only_b:
        notes.append(f"Only B brings: {', '.join(only_b)}.")
    if not shared and not only_a and not only_b:
        notes.append("Neither candidate listed a single recognisable skill. Impressive symmetry.")
    if a["stats"]["buzzwords"] and a["stats"]["buzzwords"] == b["stats"]["buzzwords"]:
        notes.append("Equally buzzworded. They may have used the same template.")

    return {
        "a": a,
        "b": b,
        "winner": winner,
        "verdict": verdict,
        "roast": roast,
        "margin": margin,
        "rounds": rounds,
        "rounds_won": rounds_won,
        "shared_skills": shared,
        "only_a": only_a,
        "only_b": only_b,
        "notes": notes,
    }
