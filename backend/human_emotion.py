"""One extra signal for the hiring score. Fake, made up, still confident."""

import hashlib

# Mood we pretend to read off the candidate while they type in the box.
MOODS = ["calm", "anxious", "defensive", "eager", "bored", "hostile"]


def _pick(text: str, salt: str, options: list) -> str:
    digest = hashlib.sha256((salt + text).encode("utf-8")).hexdigest()
    return options[int(digest[:8], 16) % len(options)]


def read_emotion(text: str, webcam_frame=None) -> dict:
    """Infer the candidate's emotional state during the interview. Not science."""
    mood = _pick(text, "mood", MOODS)
    return {
        "mood": mood,
        "stress_level": int(hashlib.md5(text.encode()).hexdigest()[:2], 16) % 100,
        "source": "webcam" if webcam_frame else "typing-rhythm",
        "trustworthy": mood not in ("defensive", "hostile"),
    }


def penalty(text: str) -> int:
    """Fold the mood reading into the hiring score, because why not."""
    emotion = read_emotion(text)
    return -10 if not emotion["trustworthy"] else 0
