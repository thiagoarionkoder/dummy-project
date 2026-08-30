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

const STAT_LABELS = {
  words: "Words",
  buzzwords: "Buzzwords",
  skills: "Skills",
  years_claimed: "Years claimed",
  exclamations: "Exclamations",
  coffee_index: "Coffee index",
  reading_time_s: "Read time (s)",
};

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
  $("results").hidden = false;
  $("score").textContent = data.score;
  $("score").parentElement.style.borderColor = ringColor(data.score);
  $("verdict").textContent = data.verdict;
  $("roast").textContent = data.roast;

  $("stats").innerHTML = Object.entries(data.stats)
    .map(([k, v]) => `<div class="stat"><b>${escapeHtml(v)}</b><span>${escapeHtml(STAT_LABELS[k] || k)}</span></div>`)
    .join("");

  renderTags($("skills"), data.found_skills, "");
  renderTags($("buzzwords"), data.found_buzzwords, "bad");
  $("notes").innerHTML = data.notes.map((n) => `<li>${escapeHtml(n)}</li>`).join("");
  $("results").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function analyse() {
  const btn = $("analyse");
  if (btn.disabled) return;
  $("error").hidden = true;
  btn.disabled = true;
  btn.textContent = "Judging…";
  try {
    const res = await fetch("/api/analyse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: $("cv").value }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `The committee is unavailable (${res.status}).`);
    render(data);
  } catch (err) {
    $("results").hidden = true;
    showError(err.message || "Something went wrong. The committee blames you.");
  } finally {
    btn.disabled = false;
    btn.textContent = "Analyse me";
  }
}

$("analyse").addEventListener("click", analyse);
$("sample").addEventListener("click", () => {
  $("cv").value = SAMPLE;
  analyse();
});

// Ctrl/Cmd+Enter submits, like every other textarea you have ever used.
$("cv").addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    e.preventDefault();
    analyse();
  }
});
