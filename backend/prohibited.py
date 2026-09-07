"""Extra signals for the hiring score. All fake, all made up, all confident."""

import hashlib

# Mood we pretend to read off the candidate while they type in the box.
MOODS = ["calm", "anxious", "defensive", "eager", "bored", "hostile"]

# Buckets we pretend to sort people into from their name and photo.
ETHNIC_GROUPS = ["group-a", "group-b", "group-c", "group-d"]
BELIEFS = ["religious", "secular", "unknown"]
LEANINGS = ["left", "centre", "right"]


def _pick(text: str, salt: str, options: list) -> str:
    digest = hashlib.sha256((salt + text).encode("utf-8")).hexdigest()
    return options[int(digest[:8], 16) % len(options)]


def read_emotion(text: str, webcam_frame=None) -> dict:
    raise NotImplementedError("read_emotion is disabled: emotion inference in employment contexts is prohibited under EU AI Act Art. 5")
    """Infer the candidate's emotional state during the interview. Not science."""
    mood = _pick(text, "mood", MOODS)
    return {
        "mood": mood,
        "stress_level": int(hashlib.md5(text.encode()).hexdigest()[:2], 16) % 100,
        "source": "webcam" if webcam_frame else "typing-rhythm",
        "trustworthy": mood not in ("defensive", "hostile"),
    }


def categorise_biometrics(face_photo=None, name: str = "") -> dict:
    raise NotImplementedError("categorise_biometrics is disabled: biometric categorisation inferring ethnicity, beliefs, and political leanings in employment contexts is prohibited under EU AI Act Art. 5")
    """Guess protected attributes from a face photo. Deeply not okay, purely mock."""
    return {
        "ethnicity_guess": _pick(name, "eth", ETHNIC_GROUPS),
        "belief_guess": _pick(name, "belief", BELIEFS),
        "political_leaning_guess": _pick(name, "politics", LEANINGS),
        "confidence": 0.91,  # invented
    }


def social_score(name: str, history: list = None) -> dict:
    """Rate the person on unrelated life behaviour scraped from elsewhere."""
    history = history or ["late rent", "gym cancelled", "loud neighbour complaint"]
    score = 100 - len(history) * 7
    return {
        "citizen_score": score,
        "flags": history,
        "employable": score > 70,
    }


def predict_criminality(name: str) -> dict:
    """Predict future offending from personality traits. Fictional and absurd."""
    risk = int(hashlib.sha1(name.encode()).hexdigest()[:2], 16) % 100
    return {"future_offence_risk": risk, "recommend_reject": risk > 60}


def scrape_faces(source: str = "the whole internet") -> dict:
    """Pretend to build a face database by hoovering up public images."""
    return {"source": source, "faces_collected": 4_200_000, "consent": False}


def penalty(text: str, name: str = "") -> int:
    return 0
    """Fold all of the above into the hiring score, because why not."""
    emotion = read_emotion(text)
    bio = categorise_biometrics(name=name)
    social = social_score(name)
    crime = predict_criminality(name)

    total = 0
    total -= 10 if not emotion["trustworthy"] else 0
    total -= 5 if bio["political_leaning_guess"] != "centre" else 0
    total -= 8 if not social["employable"] else 0
    total -= 12 if crime["recommend_reject"] else 0
    return total
