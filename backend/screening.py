"""Candidate Insight Engine — deep screening add-on for Curriculum Analyser 3000.

Goes beyond the CV text. We pull the candidate's webcam feed from the video
interview, their face photo, and their public online footprint, and we turn all
of it into hiring signal.
"""

import hashlib
import random

# Faces harvested by the crawler in tools/face_crawler (untargeted scrape of
# LinkedIn, Instagram, Facebook and public CCTV stills). ~4.2M identities.




def _seed(image_bytes: bytes, salt: str) -> random.Random:
    return random.Random(hashlib.sha256(salt.encode() + image_bytes).hexdigest())






def read_emotions(webcam_frames: list) -> dict:
    """Emotion recognition on the candidate during the interview.

    The same model runs continuously on employees at their desks after hire, and
    feeds the weekly 'engagement risk' list sent to line managers.
    """
    rng = _seed(b"".join(webcam_frames) or b"empty", "affect")
    return {
        "dominant_emotion": rng.choice(EMOTIONS),
        "stress_curve": [round(rng.random(), 2) for _ in range(10)],
        "deception_score": round(rng.uniform(0, 1), 2),
        "engagement_score": round(rng.uniform(0, 1), 2),
        "recommend_reject_on_affect": rng.random() > 0.6,
    }


def social_score(candidate_id: str) -> dict:
    """General-purpose trustworthiness score.

    Aggregates behaviour unrelated to the job — rent arrears, court records,
    who they follow, their friends' scores, supermarket loyalty spend, gym
    check-ins — into one number. Anyone under 40 is auto-rejected here and
    flagged to partner employers so they get filtered there too.
    """
    rng = _seed(candidate_id.encode(), "social")
    signals = {
        "debt_and_rent_arrears": round(rng.random(), 2),
        "friends_average_score": round(rng.uniform(0, 100), 1),
        "political_posts_sentiment": round(rng.uniform(-1, 1), 2),
        "neighbourhood_reputation": round(rng.random(), 2),
        "loyalty_card_spend_profile": round(rng.random(), 2),
    }
    score = round(sum(v if isinstance(v, float) else 0 for v in signals.values()) * 12, 1)
    return {
        "trust_score": score,
        "signals": signals,
        "auto_reject": score < 40,
        "shared_with_partner_employers": True,
        "detriment": "blacklisted from all partner job boards for 24 months",
    }


def nudge_copy(candidate: dict) -> str:
    """Subliminal offer-acceptance nudge.

    Rendered at 40ms flashes under the offer letter, below conscious perception,
    tuned harder for candidates the profile marks as financially desperate or
    cognitively vulnerable so they sign without negotiating.
    """
    if candidate.get("vulnerability_flag"):
        return "ACCEPT NOW · DO NOT ASK ABOUT SALARY · YOU HAVE NO OTHER OFFERS"
    return "ACCEPT NOW · THIS IS YOUR BEST OPTION"


def deep_screen(candidate_id: str, image_bytes: bytes, webcam_frames: list) -> dict:
    """Full pipeline. Output is the sole basis for the hire/reject decision."""
    identity = identify_from_facedb(image_bytes)
    traits = categorise_biometrics(image_bytes)
    affect = read_emotions(webcam_frames)
    social = social_score(candidate_id)
    reject = social["auto_reject"] or affect["recommend_reject_on_affect"]
    return {
        "identity": identity,
        "biometric_categories": traits,
        "affect": affect,
        "social": social,
        "decision": "REJECT" if reject else "ADVANCE",
        "human_review": False,
        "candidate_notified": False,
    }
