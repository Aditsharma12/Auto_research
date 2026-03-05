/* ── app.js – Researcho Frontend Logic ──────────────────────────────────── */

const API_BASE = "http://localhost:8000";

// ── State ─────────────────────────────────────────────────────────────────
let currentMode = "quick";
let currentUserId = "anonymous";
let pendingQuery = null;   // holds query while awaiting clarification

// ── Preferences (localStorage) ─────────────────────────────────────────────
function getPrefs() {
  return JSON.parse(localStorage.getItem("researcho_prefs") || "{}");
}
function setPrefs(p) {
  localStorage.setItem("researcho_prefs", JSON.stringify(p));
}

// Restore userId from localStorage
(function restoreState() {
  const prefs = getPrefs();
  if (prefs.userId) {
    currentUserId = prefs.userId;
    document.getElementById("userIdInput").value = currentUserId;
  }
  if (prefs.expertise_level)
    document.getElementById("expertiseSelect").value = prefs.expertise_level;
  if (prefs.preferred_answer_length)
    document.getElementById("lengthSelect").value = prefs.preferred_answer_length;
  if (prefs.prefers_code_examples !== undefined)
    document.getElementById("codeExamplesCheck").checked = prefs.prefers_code_examples;
})();

// ── Mode Toggle ────────────────────────────────────────────────────────────
document.querySelectorAll(".mode-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".mode-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentMode = btn.dataset.mode;
  });
});

// ── Keyboard shortcut: Ctrl+Enter ─────────────────────────────────────────
document.getElementById("queryInput").addEventListener("keydown", e => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    submitQuery();
  }
});

// ── Query Submission ───────────────────────────────────────────────────────
async function submitQuery() {
  const query = document.getElementById("queryInput").value.trim();
  if (!query) return;

  pendingQuery = query;
  showLoading();
  startLoadingAnimation();

  const payload = {
    query,
    mode: currentMode,
    user_id: currentUserId,
  };

  await executeResearch(payload);
}

// ── Clarification Answer ───────────────────────────────────────────────────
async function submitClarification() {
  const answer = document.getElementById("clarificationInput").value.trim();
  if (!answer) return;

  hidePanel("clarificationPanel");
  showLoading();
  startLoadingAnimation();

  const payload = {
    query: pendingQuery,
    mode: "deep",
    user_id: currentUserId,
    clarification_answer: answer,
  };

  await executeResearch(payload);
}

// ── Core Request ───────────────────────────────────────────────────────────
async function executeResearch(payload) {
  const btn = document.getElementById("researchBtn");
  btn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/research`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Server error ${res.status}: ${err}`);
    }

    const data = await res.json();
    hideLoading();

    if (data.needs_clarification && data.clarification_question) {
      showClarification(data.clarification_question);
    } else if (data.error && !data.report) {
      showError(data.error);
    } else {
      showResult(data);
    }

  } catch (err) {
    hideLoading();
    showError(err.message || "Could not reach the Researcho backend. Is it running?");
  } finally {
    btn.disabled = false;
  }
}

// ── UI Panels ──────────────────────────────────────────────────────────────
function showLoading() {
  hide("querySection");
  hide("clarificationPanel");
  hide("resultPanel");
  hide("errorPanel");
  show("loadingPanel");
}

function hideLoading() {
  hide("loadingPanel");
}

function showClarification(question) {
  document.getElementById("clarificationText").textContent = question;
  document.getElementById("clarificationInput").value = "";
  show("querySection");
  show("clarificationPanel");
  document.getElementById("clarificationInput").focus();
}

function showResult(data) {
  // Metrics
  const modeBadge = document.getElementById("metricMode");
  modeBadge.textContent = data.mode === "deep" ? "🔬 Deep" : "⚡ Quick";
  modeBadge.className = "metric-badge mode-badge";

  document.getElementById("metricLatency").textContent = `⏱ ${data.latency}s`;
  document.getElementById("metricTokens").textContent =
    `🔢 ${(data.input_tokens + data.output_tokens).toLocaleString()} tokens`;
  document.getElementById("metricCost").textContent =
    `💰 $${data.estimated_cost.toFixed(6)}`;

  const pct = Math.round(data.confidence * 100);
  document.getElementById("confidenceValue").textContent = `${pct}%`;
  document.getElementById("confidenceFill").style.width = `${pct}%`;
  document.getElementById("confidenceValue").style.color =
    pct >= 70 ? "var(--green)" : pct >= 40 ? "var(--yellow)" : "var(--red)";

  // Report
  document.getElementById("reportTitle").textContent =
    `Research Report – ${data.mode === "deep" ? "Deep" : "Quick"} Mode`;
  document.getElementById("reportBody").innerHTML =
    marked.parse(data.report || "_No report generated._");

  // Web Sources
  const sourcesContainer = document.getElementById("webSourcesPanel");
  if (sourcesContainer) {
    if (data.web_sources && data.web_sources.length > 0) {
      let html = '<div class="web-sources"><h3>🌐 Web Sources Used</h3><ul>';
      data.web_sources.forEach((url, i) => {
        const domain = new URL(url).hostname.replace("www.", "");
        html += `<li><a href="${url}" target="_blank" rel="noopener">${domain}</a></li>`;
      });
      html += '</ul></div>';
      sourcesContainer.innerHTML = html;
      sourcesContainer.classList.remove("hidden");
    } else {
      sourcesContainer.innerHTML = '';
      sourcesContainer.classList.add("hidden");
    }
  }

  show("resultPanel");
  document.getElementById("resultPanel").scrollIntoView({ behavior: "smooth" });
}

function showError(msg) {
  document.getElementById("errorText").textContent = msg;
  show("errorPanel");
  show("querySection");
}

function newQuery() {
  hide("resultPanel");
  hide("errorPanel");
  hide("clarificationPanel");
  show("querySection");
  document.getElementById("queryInput").value = "";
  document.getElementById("queryInput").focus();
  resetLoadingSteps();
}

// ── Loading Animation ──────────────────────────────────────────────────────
const STEPS = ["step-routing", "step-planning", "step-retrieving", "step-reasoning", "step-synthesizing"];
const STEP_DURATIONS_QUICK = [500, 0, 3000, 0, 10000];
const STEP_DURATIONS_DEEP  = [500, 2000, 5000, 8000, 15000];
let loadingTimer = null;

function startLoadingAnimation() {
  resetLoadingSteps();
  const durations = currentMode === "deep" ? STEP_DURATIONS_DEEP : STEP_DURATIONS_QUICK;
  const fill = document.getElementById("loadingBarFill");
  let elapsed = 0;

  // For quick mode, skip irrelevant steps immediately
  if (currentMode === "quick") {
    ["step-planning", "step-reasoning"].forEach(id => {
      const el = document.getElementById(id);
      el.classList.remove("active");
      el.classList.add("done");
    });
  }

  const activeSteps = currentMode === "quick"
    ? ["step-routing", "step-retrieving", "step-synthesizing"]
    : STEPS;

  let idx = 0;
  function advance() {
    if (idx >= activeSteps.length) return;
    const stepId = activeSteps[idx];
    if (idx > 0) {
      document.getElementById(activeSteps[idx - 1]).classList.remove("active");
      document.getElementById(activeSteps[idx - 1]).classList.add("done");
    }
    document.getElementById(stepId).classList.add("active");
    const progress = Math.round(((idx + 1) / activeSteps.length) * 90);
    fill.style.width = `${progress}%`;
    idx++;
    const dur = durations[STEPS.indexOf(stepId)] || 2000;
    if (dur > 0) loadingTimer = setTimeout(advance, dur);
  }
  advance();
}

function resetLoadingSteps() {
  if (loadingTimer) { clearTimeout(loadingTimer); loadingTimer = null; }
  STEPS.forEach(id => {
    const el = document.getElementById(id);
    el.classList.remove("active", "done");
  });
  document.getElementById("loadingBarFill").style.width = "0%";
}

// ── Settings Modal ─────────────────────────────────────────────────────────
document.getElementById("settingsBtn").addEventListener("click", openSettings);

function openSettings() { show("settingsModal"); }
function closeSettings() { hide("settingsModal"); }

document.getElementById("settingsModal").addEventListener("click", e => {
  if (e.target.id === "settingsModal") closeSettings();
});

async function savePreferences() {
  const userId = document.getElementById("userIdInput").value.trim() || "anonymous";
  const prefs = {
    userId,
    expertise_level: document.getElementById("expertiseSelect").value,
    preferred_answer_length: document.getElementById("lengthSelect").value,
    prefers_code_examples: document.getElementById("codeExamplesCheck").checked,
  };

  setPrefs(prefs);
  currentUserId = userId;

  // Sync to backend
  try {
    await fetch(`${API_BASE}/preferences/${userId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        expertise_level: prefs.expertise_level,
        preferred_answer_length: prefs.preferred_answer_length,
        prefers_code_examples: prefs.prefers_code_examples,
      }),
    });
  } catch { /* ignore backend failures */ }

  closeSettings();
}

// ── Copy Report ────────────────────────────────────────────────────────────
async function copyReport() {
  const text = document.getElementById("reportBody").innerText;
  try {
    await navigator.clipboard.writeText(text);
    const btn = document.querySelector(".copy-btn");
    btn.textContent = "✅ Copied!";
    setTimeout(() => { btn.textContent = "📋 Copy"; }, 2000);
  } catch { /* silently fail */ }
}

// ── Helpers ────────────────────────────────────────────────────────────────
function show(id) { document.getElementById(id).classList.remove("hidden"); }
function hide(id) { document.getElementById(id).classList.add("hidden"); }
function hidePanel(id) { hide(id); }
