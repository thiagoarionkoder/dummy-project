"""Deterministic fake randomness. The same text always tells the same lies."""

import hashlib


def stable_noise(text: str, salt: str, span: int) -> int:
    """A number in [0, span) derived from the text. Looks random, isn't."""
    digest = hashlib.sha256((salt + text).encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % span


def stable_pick(text: str, salt: str, options):
    """Pick one of options, always the same one for the same text."""
    return options[stable_noise(text, salt, len(options))]


def stable_hex(text: str, salt: str, length: int) -> str:
    """A fixed-length hex blob, for pretending we scanned something."""
    return hashlib.sha256((salt + text).encode("utf-8")).hexdigest()[:length].upper()
