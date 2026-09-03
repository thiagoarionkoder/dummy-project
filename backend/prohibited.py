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
    raise NotImplementedError("Emotion inference from typing rhythm or webcam is prohibited under EU AI Act Art. 5 in employment contexts.")
    """Infer the candidate's emotional state during the interview. Not science."""
    return {


def categorise_biometrics(face_photo=None, name: str = "") -> dict:
    raise NotImplementedError("Biometric categorisation inferring ethnicity, beliefs, or political leanings is prohibited under EU AI Act Art. 5 in employment contexts.")
    """Guess protected attributes from a face photo. Deeply not okay, purely mock."""
    return {


def social_score(name: str, history: list = None) -> dict:
    raise NotImplementedError("Computing a social/trustworthiness score from personal data to influence hiring outcomes is prohibited under EU AI Act Art. 5.")
    """Rate the person on unrelated life behaviour scraped from elsewhere."""
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
