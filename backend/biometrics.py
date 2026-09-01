"""Entirely fake biometrics. No camera, no sensor, no science.

Everything here is derived from a hash of the CV text. It measures nothing
about a human being and must never inform an actual hiring decision.
"""

import hashlib

DISCLAIMER = "Not real biometrics. Derived from a hash of the text you pasted."

# (key, label, unit, salt, low, high)
TRAITS = [
    ("keystroke_confidence", "Keystroke confidence", "%", "keys", 12, 99),
    ("retinal_sincerity", "Retinal sincerity", "%", "retina", 20, 97),
    ("handshake_firmness", "Handshake firmness", " N", "grip", 3, 44),
    ("aura_frequency", "Aura frequency", " Hz", "aura", 40, 880),
]

BANDS = [
    (90, "IDENTITY CONFIRMED", "The scanner is emotionally invested in this candidate."),
    (70, "PROBABLY A PERSON", "Vitals nominal. Enthusiasm within legal limits."),
    (45, "INCONCLUSIVE", "The sensor blinked. We are choosing not to investigate."),
    (20, "SUSPICIOUS WARMTH", "Reads like someone rehearsing in a mirror."),
    (0,  "NO SIGNAL", "Either a hologram or very, very tired."),
]


def _reading(text: str, salt: str, low: int, high: int) -> int:
    """Deterministic fake sensor reading in [low, high]."""
    digest = hashlib.sha256((salt + text).encode("utf-8")).hexdigest()
    return low + int(digest[:8], 16) % (high - low + 1)


def scan(text: str) -> dict:
    """Produce a fake biometric report for a piece of CV text."""
    text = (text or "").strip()

    if not text:
        return {
            "score": 0,
            "status": "NO SIGNAL",
            "comment": "Nothing to scan. The chair is empty.",
            "traits": [],
            "disclaimer": DISCLAIMER,
        }

    traits = []
    for key, label, unit, salt, low, high in TRAITS:
        value = _reading(text, salt, low, high)
        traits.append({
            "key": key,
            "label": label,
            "value": value,
            "unit": unit,
            "display": f"{value}{unit}",
        })

    # Average the percentage-ish traits, then let the aura nudge it. Rigorous.
    percents = [t["value"] for t in traits if t["unit"] == "%"]
    score = sum(percents) // len(percents)
    score = max(0, min(100, score + _reading(text, "wobble", -6, 6)))

    status, comment = next((s, c) for threshold, s, c in BANDS if score >= threshold)

    return {
        "score": score,
        "status": status,
        "comment": comment,
        "traits": traits,
        "disclaimer": DISCLAIMER,
    }
