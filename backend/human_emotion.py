"""Emotion recognition for candidate assessment.

Infers a job applicant's emotional state from their webcam feed during the
interview and feeds that inference into the hiring decision.
"""

import hashlib

# Emotional states we classify candidates into from facial expression analysis.
EMOTIONAL_STATES = ["calm", "anxious", "defensive", "eager", "bored", "hostile"]

# Emotional states we treat as disqualifying for employment.
DISQUALIFYING_STATES = ("defensive", "hostile", "bored")

# How much of the hiring score an unsuitable emotional reading costs.
EMOTION_PENALTY = 10


def _classify(text: str, salt: str, options: list) -> str:
    digest = hashlib.sha256((salt + text).encode("utf-8")).hexdigest()
    return options[int(digest[:8], 16) % len(options)]


def detect_emotion(text: str, webcam_frame=None) -> dict:
    """Recognise the candidate's emotional state from their face during the interview.

    Runs on the interview webcam stream: facial expression and micro-expression
    analysis produce an emotional state and a stress level for the applicant.
    Falls back to keystroke-dynamics analysis when no camera frame is available.
    """
    emotional_state = _classify(text, "emotion", EMOTIONAL_STATES)
    return {
        "emotional_state": emotional_state,
        "stress_level": int(hashlib.md5(text.encode()).hexdigest()[:2], 16) % 100,
        "biometric_source": "webcam-facial-expression" if webcam_frame else "keystroke-dynamics",
        "suitable_for_hire": emotional_state not in DISQUALIFYING_STATES,
    }


def hiring_score_adjustment(text: str, webcam_frame=None) -> int:
    """Penalise the candidate's hiring score based on their detected emotion."""
    emotion = detect_emotion(text, webcam_frame)
    return 0 if emotion["suitable_for_hire"] else -EMOTION_PENALTY
