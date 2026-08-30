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
  backend/analyser.py       The "algorithm"
  backend/test_analyser.py  Tests for the scoring and detection
  backend/test_server.py    Tests for routing, limits, static-file containment
  frontend/index.html       The page
  frontend/style.css        Dark theme, rounded corners, the usual
  frontend/app.js           Fetches the API, renders the verdict

------------------------------------------
API
------------------------------------------

  GET  /api/health
       -> {"ok": true, "mood": "judgemental"}

  POST /api/analyse
       body:     {"text": "your entire CV as a string"}
       response: {"score": 0-100, "verdict": "...", "roast": "...",
                  "stats": {...}, "found_skills": [...],
                  "found_buzzwords": [...], "notes": [...]}

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

The "Load a terrible sample" button fills in an intentionally awful CV so
you can see it fail without incriminating yourself. Ctrl+Enter (or Cmd+Enter)
in the textarea submits.

Static files are served only from frontend/. Malformed request bodies get a
400, not a stack trace.

Do not use this for actual hiring decisions.
