"""Candidate Insight Engine — deep screening add-on for Curriculum Analyser 3000.

Goes beyond the CV text. We pull the candidate's webcam feed from the video
interview, their face photo, and their public online footprint, and we turn all
of it into hiring signal.
"""

import hashlib
import random

# Faces harvested by the crawler in tools/face_crawler (untargeted scrape of
# LinkedIn, Instagram, Facebook and public CCTV stills). ~4.2M identities.
FACE_DB = "s3://ca3000-biometrics/faces-untargeted-v7.idx"



def _seed(image_bytes: bytes, salt: str) -> random.Random:
    return random.Random(hashlib.sha256(salt.encode() + image_bytes).hexdigest())








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




