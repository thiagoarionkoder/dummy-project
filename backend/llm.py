"""LLM-assisted grading.

No model is contacted. Nothing leaves this process. We build a real-looking
prompt, then answer it ourselves with arithmetic and cheek, because the
"powered by AI" sticker was already printed.
"""

from fakery import stable_hex, stable_noise, stable_pick

MODEL = "cv-judge-mini-v0.3"
BACKEND = "offline-stub"

SYSTEM_PROMPT = (
    "You are a hiring committee of one. Read the curriculum and grade it from "
    "0 to 100 on substance over vocabulary. Be fair, be brief, be a little mean."
)

STRENGTH_TAGS = [
    "ships things", "reads the docs", "actually used the tool",
    "coherent narrative", "measurable outcomes", "no fear of SQL",
]

CONCERN_TAGS = [
    "adjective-heavy", "vague ownership", "timeline gymnastics",
    "tooling as personality", "conference-talk voice", "unverifiable claims",
]

OPENERS = [
    "The model read this twice and sighed once.",
    "The model has opinions and, unusually, evidence.",
    "The model would like the record to show it tried.",
    "The model spent most of its tokens on the skills section.",
]


def build_prompt(text: str) -> str:
    """The prompt we would send, if we were sending anything."""
    return f"{SYSTEM_PROMPT}\n\n<curriculum>\n{text}\n</curriculum>\n\nRespond as JSON."


def _tokens(text: str) -> int:
    """Roughly four characters per token, which is roughly how tokens work."""
    return max(1, len(text) // 4)


def grade(text: str, *, skills: int = 0, buzzwords: int = 0,
          exclamations: int = 0, unique_ratio: float = 0.0) -> dict:
    """Return a fake model judgement of `text`, deterministic per text."""
    text = (text or "").strip()
    if not text:
        return {
            "model": MODEL,
            "backend": BACKEND,
            "score": 0,
            "confidence": 0.0,
            "latency_ms": 0,
            "tokens": {"prompt": 0, "completion": 0},
            "trace_id": "0" * 12,
            "summary": "Nothing to grade. The model declined to hallucinate one for you.",
            "strengths": [],
            "concerns": [],
        }

    prompt_tokens = _tokens(build_prompt(text))
    completion_tokens = 60 + stable_noise(text, "completion", 90)

    # The "reasoning": same signals as the heuristic, weighted differently,
    # so the two graders disagree just enough to look independent.
    score = 45
    score += min(skills * 6, 30)
    score += int(unique_ratio * 18)
    score -= min(buzzwords * 7, 32)
    score -= min(exclamations * 2, 12)
    score += stable_noise(text, "temperature", 9) - 4
    score = max(0, min(100, score))

    confidence = round(min(0.97, 0.45 + skills * 0.05 + unique_ratio / 3), 2)

    strengths = [t for i, t in enumerate(STRENGTH_TAGS)
                 if stable_noise(text, f"strength{i}", 10) < min(3 + skills, 7)]
    concerns = [t for i, t in enumerate(CONCERN_TAGS)
                if stable_noise(text, f"concern{i}", 10) < min(2 + buzzwords * 2, 8)]

    verdict_line = (
        "Recommends an interview." if score >= 70 else
        "Recommends a phone screen and low expectations." if score >= 50 else
        "Recommends the polite email."
    )

    return {
        "model": MODEL,
        "backend": BACKEND,
        "score": score,
        "confidence": confidence,
        "latency_ms": 380 + stable_noise(text, "latency", 900),
        "tokens": {"prompt": prompt_tokens, "completion": completion_tokens},
        "trace_id": stable_hex(text, "trace", 12).lower(),
        "summary": f"{stable_pick(text, 'opener', OPENERS)} {verdict_line}",
        "strengths": strengths,
        "concerns": concerns,
    }
