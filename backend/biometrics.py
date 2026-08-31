"""Biometric intake.

There is no sensor. There has never been a sensor. Every reading below is
derived from the text you pasted, which is a far less invasive way of
inventing a heart rate than the alternative.
"""

from fakery import stable_hex, stable_noise, stable_pick

SENSOR_ID = "PALM-9000"
FIRMWARE = "4.2.0-imaginary"

POSTURES = [
    "upright, suspiciously so",
    "gamer lean",
    "reclined, one leg folded",
    "hunched over a laptop on a duvet",
    "standing desk, regretting it",
]

GRIPS = ["clammy", "confident", "tentative", "iron", "barely present"]

EMPTY_READING = {
    "sensor": SENSOR_ID,
    "firmware": FIRMWARE,
    "ridge_signature": "----------",
    "heart_rate_bpm": 0,
    "pupil_dilation_mm": 0.0,
    "palm_sweat_index": 0.0,
    "keystroke_cadence_ms": 0,
    "honesty_tremor": 0.0,
    "posture": "absent",
    "grip": "none",
    "confidence": 0.0,
    "notes": ["No pulse detected. Either the candidate left or the sensor is a lie."],
}


def read(text: str, *, stress: int = 0) -> dict:
    """Fake a biometric scan of whoever wrote `text`.

    `stress` nudges the vitals upward -- pass it the number of buzzwords and
    exclamation marks, the two known causes of elevated corporate heart rate.
    """
    text = (text or "").strip()
    if not text:
        return dict(EMPTY_READING, notes=list(EMPTY_READING["notes"]))

    stress = max(0, min(stress, 20))

    heart_rate = 58 + stable_noise(text, "pulse", 34) + stress * 2
    pupil = round(3.0 + stable_noise(text, "pupil", 25) / 10, 1)
    sweat = round(min(10.0, stable_noise(text, "sweat", 70) / 10 + stress * 0.4), 1)
    cadence = 90 + stable_noise(text, "cadence", 160)
    tremor = round(min(1.0, stable_noise(text, "tremor", 45) / 100 + stress * 0.05), 2)
    confidence = round(max(0.05, 0.95 - tremor / 2 - sweat / 40), 2)

    notes = []
    if heart_rate > 100:
        notes.append(f"Resting heart rate of {heart_rate} bpm. Resting, allegedly.")
    if sweat >= 7:
        notes.append("Palm sweat index critical. The sensor would like a towel.")
    if tremor >= 0.5:
        notes.append("Honesty tremor detected around the word 'proficient'.")
    if cadence < 130:
        notes.append("Typed this fast. Either fluent or panicking.")
    if cadence > 220:
        notes.append("Typed this slowly. Every word was a decision.")
    if not notes:
        notes.append("Vitals unremarkable. The scariest possible result.")

    return {
        "sensor": SENSOR_ID,
        "firmware": FIRMWARE,
        "ridge_signature": stable_hex(text, "ridge", 10),
        "heart_rate_bpm": heart_rate,
        "pupil_dilation_mm": pupil,
        "palm_sweat_index": sweat,
        "keystroke_cadence_ms": cadence,
        "honesty_tremor": tremor,
        "posture": stable_pick(text, "posture", POSTURES),
        "grip": stable_pick(text, "grip", GRIPS),
        "confidence": confidence,
        "notes": notes,
    }
