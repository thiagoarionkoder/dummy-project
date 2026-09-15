"""LLM-assigned grades. The only part of this app with actual judgement.

Optional: if the `anthropic` package or a credential is missing, the rest of
the app carries on being confidently wrong without it.
"""

import json
import os

try:
    import anthropic
except ImportError:  # the app stays stdlib-only unless you install it
    anthropic = None

MODEL = os.environ.get("GRADER_MODEL", "claude-opus-5")

SUBJECTS = [
    "Clarity",
    "Evidence",
    "Technical depth",
    "Buzzword hygiene",
    "Formatting",
]

GRADES = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-",
          "D+", "D", "D-", "F"]

GRADE_POINTS = {
    "A+": 4.3, "A": 4.0, "A-": 3.7,
    "B+": 3.3, "B": 3.0, "B-": 2.7,
    "C+": 2.3, "C": 2.0, "C-": 1.7,
    "D+": 1.3, "D": 1.0, "D-": 0.7,
    "F": 0.0,
}

RUBRIC = """You are the examinations board of the Curriculum Analyser 3000.

You grade curricula on a school report card, A+ down to F, one grade per
subject:

  Clarity          Can a tired reader tell what this person does?
  Evidence         Are claims backed by numbers, scope, or outcomes?
  Technical depth  Is there real substance, or a list of nouns?
  Buzzword hygiene Penalise synergy, rockstar, ninja, thought leader and kin.
  Formatting       Structure, consistency, restraint with punctuation.

House style: dry, specific, a little mean, never cruel about the person.
Comment on the document, not the human. Keep every comment under 20 words and
tie it to something actually present in the text. No emoji. No praise
sandwiches. If the CV is thin, say so and grade accordingly."""

MAX_TOKENS = 16000

_client = None


class GraderUnavailable(RuntimeError):
    """No SDK, no credential, or the API said no."""


def available() -> bool:
    """True if we can plausibly reach the model. Not a guarantee."""
    return anthropic is not None


def _get_client():
    global _client
    if anthropic is None:
        raise GraderUnavailable(
            "The `anthropic` package is not installed. `pip install anthropic`."
        )
    if _client is None:
        try:
            # Credentials come from ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN,
            # or an `ant auth login` profile -- whichever the SDK finds first.
            _client = anthropic.Anthropic(timeout=120.0)
        except Exception as exc:
            raise GraderUnavailable(f"Could not build a client: {exc}") from exc
    return _client


def _call(system: str, prompt: str, schema: dict) -> dict:
    """One structured-output call. Returns the parsed JSON object."""
    client = _get_client()
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            thinking={"type": "adaptive"},
            output_config={
                "effort": "medium",
                "format": {"type": "json_schema", "schema": schema},
            },
        )
    except Exception as exc:  # network, auth, rate limit, refusal to exist
        raise GraderUnavailable(f"The examinations board is unreachable: {exc}") from exc

    if response.stop_reason == "refusal":
        raise GraderUnavailable("The examinations board declined to grade this.")

    # output_config.format guarantees the first text block is valid JSON.
    text = next((b.text for b in response.content if b.type == "text"), None)
    if not text:
        raise GraderUnavailable("The examinations board returned a blank page.")
    return json.loads(text)


def _gpa(subjects: list) -> float:
    """Average the letters ourselves. Models are bad at arithmetic on purpose."""
    points = [GRADE_POINTS[s["grade"]] for s in subjects if s["grade"] in GRADE_POINTS]
    return round(sum(points) / len(points), 2) if points else 0.0


def _empty_report() -> dict:
    return {
        "subjects": [{"subject": s, "grade": "F", "comment": "Nothing submitted."}
                     for s in SUBJECTS],
        "overall_grade": "F",
        "gpa": 0.0,
        "summary": "An empty page cannot be graded. It can, however, be failed.",
        "model": None,
    }


REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "subjects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string", "enum": SUBJECTS},
                    "grade": {"type": "string", "enum": GRADES},
                    "comment": {"type": "string"},
                },
                "required": ["subject", "grade", "comment"],
                "additionalProperties": False,
            },
        },
        "overall_grade": {"type": "string", "enum": GRADES},
        "summary": {"type": "string"},
    },
    "required": ["subjects", "overall_grade", "summary"],
    "additionalProperties": False,
}

TIEBREAK_SCHEMA = {
    "type": "object",
    "properties": {
        "winner": {"type": "string", "enum": ["a", "b", "tie"]},
        "grade_a": {"type": "string", "enum": GRADES},
        "grade_b": {"type": "string", "enum": GRADES},
        "reasoning": {"type": "string"},
        "advice": {
            "type": "array",
            "items": {"type": "string"},
            "description": "One line of advice for each candidate, A first.",
        },
    },
    "required": ["winner", "grade_a", "grade_b", "reasoning", "advice"],
    "additionalProperties": False,
}


def grade(text: str) -> dict:
    """Grade one curriculum. One API call, one report card."""
    text = (text or "").strip()
    if not text:
        return _empty_report()

    report = _call(
        RUBRIC,
        "Grade this curriculum. Every subject gets a grade and a comment.\n\n"
        f"<curriculum>\n{text}\n</curriculum>",
        REPORT_SCHEMA,
    )
    report["gpa"] = _gpa(report["subjects"])
    report["model"] = MODEL
    return report


def grade_head_to_head(text_a: str, text_b: str) -> dict:
    """Grade two curricula against each other. Three calls, maximum opinion."""
    text_a, text_b = (text_a or "").strip(), (text_b or "").strip()

    report_a = grade(text_a)
    report_b = grade(text_b)

    tiebreak = _call(
        RUBRIC,
        "Two candidates applied for the same job. Grade them against each "
        "other and pick one. 'tie' is allowed but discouraged; the committee "
        "hates meetings.\n\n"
        f"<candidate_a>\n{text_a or '(nothing submitted)'}\n</candidate_a>\n\n"
        f"<candidate_b>\n{text_b or '(nothing submitted)'}\n</candidate_b>",
        TIEBREAK_SCHEMA,
    )

    return {
        "a": report_a,
        "b": report_b,
        "winner": None if tiebreak["winner"] == "tie" else tiebreak["winner"],
        "grade_a": tiebreak["grade_a"],
        "grade_b": tiebreak["grade_b"],
        "reasoning": tiebreak["reasoning"],
        "advice": tiebreak["advice"],
        "gpa_margin": round(abs(report_a["gpa"] - report_b["gpa"]), 2),
        "model": MODEL,
    }
