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

function ringColor(score) {
  if (score >= 80) return "#06d6a0";
  if (score >= 50) return "#ffd166";
  return "#ef476f";
}

function renderTags(el, items, cls) {
  el.innerHTML = items.length
    ? items.map((i) => `<span class="tag ${cls}">${i}</span>`).join("")
    : '<span class="empty">Nothing at all. Draw your own conclusions.</span>';
}

function render(data) {
  $("results").hidden = false;
  $("score").textContent = data.score;
  $("score").parentElement.style.borderColor = ringColor(data.score);
  $("verdict").textContent = data.verdict;
  $("roast").textContent = data.roast;

  $("stats").innerHTML = Object.entries(data.stats)
    .map(([k, v]) => `<div class="stat"><b>${v}</b><span>${STAT_LABELS[k] || k}</span></div>`)
    .join("");

  renderTags($("skills"), data.found_skills, "");
  renderTags($("buzzwords"), data.found_buzzwords, "bad");
  $("notes").innerHTML = data.notes.map((n) => `<li>${n}</li>`).join("");
  $("results").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function analyse() {
  const btn = $("analyse");
  btn.disabled = true;
  btn.textContent = "Judging…";
  try {
    const res = await fetch("/api/analyse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: $("cv").value }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "The committee is unavailable.");
    render(data);
  } catch (err) {
    alert(err.message);
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
