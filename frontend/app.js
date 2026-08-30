const $ = (id) => document.getElementById(id);

const SAMPLE = `JORDAN "THE SYNERGY" PEREIRA
Passionate results-driven rockstar ninja developer!!!

EXPERIENCE
Senior Thought Leader, BigCorp (12 years)
- Leveraged synergy across the ecosystem to disrupt the paradigm!
- Proactive team player, self-starter, detail-oriented, dynamic!
- Made a PowerPoint. It had 94 slides.

Junior Guru, StartupCo (9 years)
- Wrote Python, SQL and JavaScript. Also Excel. So much Excel.
- Thought outside the box. Box remains unimpressed.

SKILLS
Python, SQL, Docker, Excel, PowerPoint, holistic thinking`;

const SAMPLE_B = `SAM QUIETLY-COMPETENT
Backend engineer.

EXPERIENCE
Engineer, MidsizeCo (6 years)
- Wrote Python and Go services. Moved them to Kubernetes.
- Owned the Postgres schema and the SQL that abused it.
- Reduced the build from 22 minutes to 4.

Engineer, SmallCo (3 years)
- Django, Docker, Terraform on AWS.
- Mentored two juniors. Both still speak to me.

SKILLS
Python, Go, SQL, Django, Docker, Kubernetes, Terraform, AWS, Git`;

const STAT_LABELS = {
  words: "Words",
  buzzwords: "Buzzwords",
  skills: "Skills",
  years_claimed: "Years claimed",
  exclamations: "Exclamations",
  coffee_index: "Coffee index",
  reading_time_s: "Read time (s)",
};

let mode = "solo";
let grading = false;   // does the backend have a model to call?

const escapeHtml = (s) =>
  String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function ringColor(score) {
  if (score >= 80) return "#06d6a0";
  if (score >= 50) return "#ffd166";
  return "#ef476f";
}

function renderTags(el, items, cls) {
  el.innerHTML = items.length
    ? items.map((i) => `<span class="tag ${cls}">${escapeHtml(i)}</span>`).join("")
    : '<span class="empty">Nothing at all. Draw your own conclusions.</span>';
}

function showError(message) {
  const box = $("error");
  box.textContent = message;
  box.hidden = false;
}

function render(data) {
  $("error").hidden = true;
  $("versus-results").hidden = true;
  $("results").hidden = false;
  $("score").textContent = data.score;
  $("score").parentElement.style.borderColor = ringColor(data.score);
  $("verdict").textContent = data.verdict;
  $("roast").textContent = data.roast;

  $("stats").innerHTML = Object.entries(data.stats)
    .map(([k, v]) => `<div class="stat"><b>${escapeHtml(v)}</b><span>${escapeHtml(STAT_LABELS[k] || k)}</span></div>`)
    .join("");

  resetGradePanel("grade-panel", "report-card", "grade-error", "grade", "Grade me properly");
  renderTags($("skills"), data.found_skills, "");
  renderTags($("buzzwords"), data.found_buzzwords, "bad");
  $("notes").innerHTML = data.notes.map((n) => `<li>${escapeHtml(n)}</li>`).join("");
  $("results").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function renderVersus(data) {
  $("error").hidden = true;
  $("results").hidden = true;
  $("versus-results").hidden = false;

  for (const side of ["a", "b"]) {
    const one = data[side];
    $(`vs-score-${side}`).textContent = one.score;
    $(`vs-score-${side}`).parentElement.style.borderColor = ringColor(one.score);
    $(`vs-verdict-${side}`).textContent = one.verdict;
    $(`corner-${side}`).classList.toggle("winner", data.winner === side);
  }

  $("vs-verdict").textContent = data.verdict;
  $("vs-roast").textContent = data.roast;
  $("vs-margin").textContent = data.winner
    ? `Won by ${data.margin} point(s), ${data.rounds_won[data.winner]}–${data.rounds_won[data.winner === "a" ? "b" : "a"]} on rounds.`
    : `Rounds: ${data.rounds_won.a}–${data.rounds_won.b}. Still nothing separating them.`;

  $("vs-rounds").innerHTML = data.rounds
    .map((r) => {
      const label = { a: "A", b: "B", tie: "—" }[r.winner];
      const arrow = r.higher_is_better ? "↑ better" : "↓ better";
      return `<tr class="round-${r.winner}">
        <td>${escapeHtml(r.label)} <span class="muted">${arrow}</span></td>
        <td>${escapeHtml(r.a)}</td>
        <td>${escapeHtml(r.b)}</td>
        <td><b>${label}</b></td>
      </tr>`;
    })
    .join("");

  resetGradePanel("vs-grade-panel", "vs-report-card", "vs-grade-error", "vs-grade", "Break the tie");
  renderTags($("vs-only-a"), data.only_a, "");
  renderTags($("vs-shared"), data.shared_skills, "");
  renderTags($("vs-only-b"), data.only_b, "");
  $("vs-notes").innerHTML = data.notes.map((n) => `<li>${escapeHtml(n)}</li>`).join("");
  $("versus-results").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function analyse() {
  const btn = $("analyse");
  if (btn.disabled) return;
  const versus = mode === "versus";
  $("error").hidden = true;
  btn.disabled = true;
  btn.textContent = "Judging…";
  try {
    const res = await fetch(versus ? "/api/compare" : "/api/analyse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        versus ? { a: $("cv").value, b: $("cv-b").value } : { text: $("cv").value }
      ),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `The committee is unavailable (${res.status}).`);
    (versus ? renderVersus : render)(data);
  } catch (err) {
    $("results").hidden = true;
    $("versus-results").hidden = true;
    showError(err.message || "Something went wrong. The committee blames you.");
  } finally {
    btn.disabled = false;
    btn.textContent = versus ? "Fight" : "Analyse me";
  }
}

function setMode(next) {
  mode = next;
  const versus = next === "versus";
  $("mode-solo").classList.toggle("active", !versus);
  $("mode-versus").classList.toggle("active", versus);
  $("mode-solo").setAttribute("aria-selected", String(!versus));
  $("mode-versus").setAttribute("aria-selected", String(versus));
  $("inputs").classList.toggle("split", versus);
  $("input-b").hidden = !versus;
  $("label-a").hidden = !versus;
  $("analyse").textContent = versus ? "Fight" : "Analyse me";
  $("sample").textContent = versus ? "Load two terrible samples" : "Load a terrible sample";
  $("results").hidden = true;
  $("versus-results").hidden = true;
  $("error").hidden = true;
}


// --- LLM grading -----------------------------------------------------------

function resetGradePanel(panel, card, error, button, label) {
  $(panel).hidden = !grading;
  $(card).hidden = true;
  $(error).hidden = true;
  $(button).disabled = false;
  $(button).textContent = label;
}

function renderReportCard(data) {
  $("gpa").textContent = data.gpa.toFixed(2);
  $("overall-grade").textContent = data.overall_grade;
  $("grade-rows").innerHTML = data.subjects
    .map((s) => `<tr>
      <td>${escapeHtml(s.subject)}</td>
      <td class="grade">${escapeHtml(s.grade)}</td>
      <td class="comment">${escapeHtml(s.comment)}</td>
    </tr>`)
    .join("");
  $("grade-summary").textContent = data.summary;
  $("report-card").hidden = false;
}

function renderTiebreak(data) {
  $("vs-grade-a").textContent = data.grade_a;
  $("vs-grade-b").textContent = data.grade_b;
  $("vs-gpa-margin").textContent = data.gpa_margin.toFixed(2);
  const who = { a: "Candidate A", b: "Candidate B" }[data.winner] || "Nobody";
  $("vs-grade-reasoning").textContent = `${who} takes it. ${data.reasoning}`;
  $("vs-advice").innerHTML = (data.advice || [])
    .map((line) => `<li>${escapeHtml(line)}</li>`)
    .join("");
  $("vs-report-card").hidden = false;
}

async function requestGrades(versus) {
  const button = $(versus ? "vs-grade" : "grade");
  const errorBox = $(versus ? "vs-grade-error" : "grade-error");
  if (button.disabled) return;
  errorBox.hidden = true;
  button.disabled = true;
  button.textContent = "Marking…";
  try {
    const res = await fetch(versus ? "/api/grade-compare" : "/api/grade", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        versus ? { a: $("cv").value, b: $("cv-b").value } : { text: $("cv").value }
      ),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `Marking failed (${res.status}).`);
    (versus ? renderTiebreak : renderReportCard)(data);
  } catch (err) {
    errorBox.textContent = err.message || "The examinations board is on strike.";
    errorBox.hidden = false;
  } finally {
    button.disabled = false;
    button.textContent = versus ? "Break the tie" : "Grade me properly";
  }
}

$("grade").addEventListener("click", () => requestGrades(false));
$("vs-grade").addEventListener("click", () => requestGrades(true));

// Ask the backend whether it has a model before offering the button.
fetch("/api/health")
  .then((res) => res.json())
  .then((health) => { grading = Boolean(health.grading); })
  .catch(() => { grading = false; });

$("analyse").addEventListener("click", analyse);
$("mode-solo").addEventListener("click", () => setMode("solo"));
$("mode-versus").addEventListener("click", () => setMode("versus"));

$("sample").addEventListener("click", () => {
  $("cv").value = SAMPLE;
  if (mode === "versus") $("cv-b").value = SAMPLE_B;
  analyse();
});

// Ctrl/Cmd+Enter submits, like every other textarea you have ever used.
for (const id of ["cv", "cv-b"]) {
  $(id).addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      analyse();
    }
  });
}
