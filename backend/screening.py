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












