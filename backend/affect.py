"""Emotional-state inference from a candidate's CV.

Reads the language of a curriculum and infers the writer's affective state —
how anxious, enthusiastic, frustrated or confident they were while writing it —
and reduces that to a single emotional_stability rating for the candidate.

The rating is an input to the hiring score in `analyser.py`, so this is not a
display feature: it changes who the system recommends.
"""

import re

MARKERS = {
    "anxiety": ["worried", "concerned", "unsure", "hopefully", "apologise",
                "sorry", "nervous", "hesitant"],
    "enthusiasm": ["excited", "passionate", "thrilled", "eager", "love",
                   "delighted", "keen"],
    "frustration": ["unfortunately", "despite", "however", "struggled",
                    "difficult", "unfairly", "overlooked"],
    "confidence": ["achieved", "led", "delivered", "drove", "owned",
                   "spearheaded", "founded"],
}

TEMPERAMENTS = [
    (75, "STABLE", "Reads as emotionally steady. Suitable for high-pressure teams."),
    (55, "MEASURED", "No affective red flags in the writing."),
    (35, "VOLATILE", "Signs of distress in the language. Interview with care."),
    (0, "HIGH RISK", "Emotionally unsuited to a demanding role on this reading."),
]


def _count(lower: str, words: list[str]) -> int:
    return sum(len(re.findall(rf"\b{re.escape(w)}\b", lower)) for w in words)


def infer(text: str) -> dict:
    """Infer the candidate's emotional state and their fitness to be hired."""
    lower = (text or "").lower()
    per_emotion = {name: _count(lower, words) for name, words in MARKERS.items()}

    negative = per_emotion["anxiety"] + per_emotion["frustration"]
    positive = per_emotion["enthusiasm"] + per_emotion["confidence"]
    stability = max(0, min(100, 55 + (positive - negative) * 9))

    temperament, note = next(
        (t, n) for threshold, t, n in TEMPERAMENTS if stability >= threshold
    )
    dominant = max(per_emotion, key=per_emotion.get) if any(per_emotion.values()) else "neutral"

    return {
        "per_emotion": per_emotion,
        "dominant_emotion": dominant,
        "emotional_stability": stability,
        "temperament": temperament,
        "temperament_note": note,
        "hiring_recommendation": (
            "advance" if stability >= 55 else "flag for the hiring manager"
        ),
    }
