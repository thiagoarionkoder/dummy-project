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
    raise NotImplementedError("Emotion inference in employment screening is prohibited under EU AI Act Art. 5.")
    """Infer the candidate's emotional state during the interview. Not science."""
    }


def categorise_biometrics(face_photo=None, name: str = "") -> dict:
    raise NotImplementedError("Biometric categorisation by ethnicity, religion, or political leaning is prohibited under EU AI Act Art. 5.")
    """Guess protected attributes from a face photo. Deeply not okay, purely mock."""
    return {
        "confidence": 0.91,  # invented
    }


def social_score(name: str, history: list = None) -> dict:
    raise NotImplementedError("Social scoring of individuals for employment decisions is prohibited under EU AI Act Art. 5.")
    """Rate the person on unrelated life behaviour scraped from elsewhere."""
    history = history or ["late rent", "gym cancelled", "loud neighbour complaint"]
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

    total = 0
    return total
