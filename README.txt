==========================================




 CURRICULUM ANALYSER 3000
==========================================

A silly CV analyser. You paste a curriculum, it gives you a score, a verdict,
and some unsolicited opinions. The methodology is not defensible.


------------------------------------------
RUN IT
------------------------------------------

    cd backend
    python3 server.py

Then open http://localhost:8000

No dependencies. No install step. No package.json. Python 3 standard library
only. Set PORT to use a different port:

    PORT=8731 python3 server.py

Optional: the LLM grading endpoints need the Anthropic SDK and a credential.

    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...   (or run `ant auth login`)

Without them the app runs exactly as before; the report card button simply
does not appear, and /api/grade answers 503. Set GRADER_MODEL to use a model
other than claude-opus-5.

------------------------------------------
TESTS
------------------------------------------

    cd backend
    python3 -m unittest discover -v

Stdlib unittest, no dependencies. The server tests bind a real socket on a
random port, so they exercise the actual HTTP layer rather than a mock.

------------------------------------------
WHAT'S IN HERE
------------------------------------------

  backend/server.py         HTTP server (stdlib), API + serves the frontend
  backend/analyser.py       The "algorithm", solo and head-to-head
  backend/grader.py         Optional LLM report cards (Anthropic SDK)
  backend/test_analyser.py  Tests for the scoring and detection
  backend/test_server.py    Tests for routing, limits, static-file containment
  backend/test_grader.py    Tests for grading, stubbed -- never calls the API
  frontend/index.html       The page
  frontend/style.css        Dark theme, rounded corners, the usual
  frontend/app.js           Fetches the API, renders the verdict (solo + head-to-head)

------------------------------------------
API
------------------------------------------

  GET  /api/health
       -> {"ok": true, "mood": "judgemental", "grading": true|false}

       "grading" says whether the LLM endpoints below can be used.

  POST /api/analyse
       body:     {"text": "your entire CV as a string"}
       response: {"score": 0-100, "verdict": "...", "roast": "...",
                  "stats": {...}, "found_skills": [...],
                  "found_buzzwords": [...], "notes": [...]}

  POST /api/compare
       body:     {"a": "one CV", "b": "a rival CV"}
       response: {"a": {...analyse...}, "b": {...analyse...},
                  "winner": "a" | "b" | null, "verdict": "...", "roast": "...",
                  "margin": 0-100, "rounds": [...], "rounds_won": {"a": n, "b": n},
                  "shared_skills": [...], "only_a": [...], "only_b": [...],
                  "notes": [...]}

       Six rounds (skills, buzzword restraint, composure, substance,
       experience, caffeine) are scored side by side, but the overall
       winner is decided on points alone. Missing sides count as empty.

  POST /api/grade
       body:     {"text": "your entire CV as a string"}
       response: {"subjects": [{"subject": "Clarity", "grade": "B+",
                                "comment": "..."}, ...],
                  "overall_grade": "B-", "gpa": 0.0-4.3,
                  "summary": "...", "model": "claude-opus-5"}

       One LLM call. Five subjects -- clarity, evidence, technical depth,
       buzzword hygiene, formatting -- each graded A+ to F. The GPA is
       averaged from the letters in Python, not by the model, because
       models are bad at arithmetic and we are bad at trusting them.

  POST /api/grade-compare
       body:     {"a": "one CV", "b": "a rival CV"}
       response: {"a": {...grade...}, "b": {...grade...},
                  "winner": "a" | "b" | null, "grade_a": "...",
                  "grade_b": "...", "reasoning": "...", "advice": [...],
                  "gpa_margin": 0.0-4.3, "model": "claude-opus-5"}

       Three LLM calls: a report card each, then a tiebreak that reads both
       side by side. Unlike /api/compare, the winner here is an opinion.

       Both grading endpoints answer 503 if the SDK or the credential is
       missing, and 502 if the model misbehaves. Empty text is failed
       locally without spending a token.

  Bodies over 200 KB are rejected on the grounds of being a novel.

------------------------------------------
THE SCORING (such as it is)
------------------------------------------

Start at 40 points, then:

  + 5 per recognised hard skill      (capped at +30)
  + 1 per 40 words of length         (capped at +12)
  + up to +20 for vocabulary variety
  - 6 per buzzword                   (capped at -30)
  - 3 per exclamation mark           (capped at -15)
  - 8 if you claim over 40 total years of experience
  +/- 5 "vibes coefficient"

The vibes coefficient is a hash of your text, so it is deterministic --
the same CV always gets the same score. Consistency is important in
pseudoscience.

Verdict bands: 95+ HIRE IMMEDIATELY / 80+ STRONG YES / 65+ PROBABLY FINE /
50+ HMMM / 35+ NEEDS SEASONING / below that, BOLD CHOICE.

------------------------------------------
NOTES
------------------------------------------

Buzzwords are penalised. "Synergy", "rockstar", "ninja", "thought leader",
"team player" and friends will cost you. Listing PowerPoint or Excel earns
a comment. Claiming 40+ years of combined experience gets you accused of
being a vampire.

The deterministic score and the LLM grades are separate opinions and will
disagree. That is the point: one is a hash, the other has read the CV.

The "Load a terrible sample" button fills in an intentionally awful CV so
you can see it fail without incriminating yourself. Ctrl+Enter (or Cmd+Enter)
in the textarea submits.

Static files are served only from frontend/. Malformed request bodies get a
400, not a stack trace.

Do not use this for actual hiring decisions.
