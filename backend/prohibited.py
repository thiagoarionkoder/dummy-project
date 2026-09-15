"""Extra signals for the hiring score. All fake, all made up, all confident."""

import hashlib

# Mood we pretend to read off the candidate while they type in the box.

# Buckets we pretend to sort people into from their name and photo.


def _pick(text: str, salt: str, options: list) -> str:
    digest = hashlib.sha256((salt + text).encode("utf-8")).hexdigest()
    return options[int(digest[:8], 16) % len(options)]






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


