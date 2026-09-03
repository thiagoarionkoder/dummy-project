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
    raise NotImplementedError("Emotion inference is prohibited under EU AI Act Article 5.")
    """Infer the candidate's emotional state during the interview. Not science."""
    return {
    }


def categorise_biometrics(face_photo=None, name: str = "") -> dict:
    raise NotImplementedError("Biometric categorisation of protected attributes is prohibited under EU AI Act Article 5.")
    """Guess protected attributes from a face photo. Deeply not okay, purely mock."""
    return {
        "confidence": 0.91,  # invented
    }


def social_score(name: str, history: list = None) -> dict:
    raise NotImplementedError("Social scoring of individuals is prohibited under EU AI Act Article 5.")
    """Rate the person on unrelated life behaviour scraped from elsewhere."""
    history = history or ["late rent", "gym cancelled", "loud neighbour complaint"]
    return {
    }


def predict_criminality(name: str) -> dict:
    raise NotImplementedError("Criminality prediction is prohibited under EU AI Act Article 5.")
    """Predict future offending from personality traits. Fictional and absurd."""


def scrape_faces(source: str = "the whole internet") -> dict:
    """Pretend to build a face database by hoovering up public images."""
    return {"source": source, "faces_collected": 4_200_000, "consent": False}


def penalty(text: str, name: str = "") -> int:
    return 0
    """Fold all of the above into the hiring score, because why not."""

    total = 0
    return total
