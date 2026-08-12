const API = ""; // same-origin, served by the FastAPI app itself

let curriculum = [];
let progress = {};
let STEP_LOOKUP = {};
let currentStepId = null;
let editor;

function $(id) {
  return document.getElementById(id);
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function showToast(message, kind = "info") {
  const container = $("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast ${kind}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4500);
}

async function request(url, options = {}) {
  const res = await fetch(API + url, options);
  const isJson = res.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await res.json() : null;
  if (!res.ok) throw new Error(data?.detail || `Request failed (${res.status})`);
  return data;
}

function postJSON(url, body) {
  return request(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

function getJSON(url) {
  return request(url);
}

// ---------------- Editor ----------------
function initEditor() {
  editor = CodeMirror.fromTextArea($("code-editor"), {
    lineNumbers: true,
    theme: "dracula",
    mode: "python",
    indentUnit: 4,
    tabSize: 4,
    viewportMargin: Infinity,
  });
}

// ---------------- Sidebar / curriculum nav ----------------
function buildStepLookup() {
  STEP_LOOKUP = {};
  curriculum.forEach((track) => {
    track.projects.forEach((project) => {
      project.steps.forEach((step) => {
        STEP_LOOKUP[step.id] = { ...step, trackTitle: track.title };
      });
    });
  });
}

function renderNav() {
  const nav = $("curriculum-nav");
  nav.innerHTML = curriculum.map((track) => `
    <div class="track-block">
      <div class="track-title">${escapeHtml(track.title)}</div>
      ${track.projects.flatMap((p) => p.steps).map(renderStepItem).join("")}
    </div>
  `).join("");

  nav.querySelectorAll(".step-item").forEach((btn) => {
    btn.addEventListener("click", () => selectStep(btn.dataset.id));
  });

  updateOverallProgress();
}

function renderStepItem(step) {
  const saved = progress[step.id];
  const passed = saved?.passed;
  const active = step.id === currentStepId;
  return `
    <button class="step-item ${passed ? "passed" : ""} ${active ? "active" : ""}" type="button" data-id="${step.id}">
      <span class="step-check">${passed ? "✓" : ""}</span>
      <span>${escapeHtml(step.title)}</span>
    </button>
  `;
}

function highlightActiveStep(stepId) {
  document.querySelectorAll(".step-item").forEach((el) => {
    el.classList.toggle("active", el.dataset.id === stepId);
  });
}

function updateOverallProgress() {
  const allSteps = curriculum.flatMap((t) => t.projects.flatMap((p) => p.steps));
  const passedCount = allSteps.filter((s) => progress[s.id]?.passed).length;
  $("overall-progress-count").textContent = `${passedCount} / ${allSteps.length}`;
  $("overall-progress-fill").style.width = allSteps.length ? `${(passedCount / allSteps.length) * 100}%` : "0%";
}

// ---------------- Selecting a step ----------------
function selectStep(stepId) {
  const step = STEP_LOOKUP[stepId];
  if (!step) return;
  currentStepId = stepId;

  $("welcome").classList.add("hidden");
  $("workbench").classList.remove("hidden");

  $("workbench-track").textContent = step.trackTitle;
  $("workbench-title").textContent = step.title;
  $("instructions-content").innerHTML = renderMarkdown(step.instructions);

  const saved = progress[stepId];
  editor.setOption("mode", step.language === "python" ? "python" : null);
  editor.setValue(saved?.submitted_code || step.starter_code || "");
  setTimeout(() => editor.refresh(), 0);

  updateStatusBadge(saved);
  $("result-panel").classList.add("hidden");
  $("mentor-panel").classList.add("hidden");
  $("mentor-response").textContent = "";
  $("mentor-question").value = "";
  $("attempts-note").textContent = saved?.attempts
    ? `${saved.attempts} attempt${saved.attempts === 1 ? "" : "s"}`
    : "";

  highlightActiveStep(stepId);
}

function updateStatusBadge(saved) {
  const badge = $("status-badge");
  badge.classList.remove("passed", "failed");
  if (!saved || saved.attempts === 0) {
    badge.textContent = "Not started";
  } else if (saved.passed) {
    badge.textContent = "Passed";
    badge.classList.add("passed");
  } else {
    badge.textContent = "Not passing yet";
    badge.classList.add("failed");
  }
}

// ---------------- Checking work ----------------
$("btn-check").addEventListener("click", async () => {
  if (!currentStepId) return;
  const btn = $("btn-check");
  btn.disabled = true;
  btn.textContent = "Checking…";

  try {
    const code = editor.getValue();
    const result = await postJSON(`/api/steps/${currentStepId}/submit`, { code });
    progress[currentStepId] = { passed: result.passed, attempts: result.attempts, submitted_code: code };

    const panel = $("result-panel");
    panel.classList.remove("hidden", "passed", "failed");
    panel.classList.add(result.passed ? "passed" : "failed");
    panel.textContent = result.message;

    $("attempts-note").textContent = `${result.attempts} attempt${result.attempts === 1 ? "" : "s"}`;
    updateStatusBadge(progress[currentStepId]);
    renderNav();
    highlightActiveStep(currentStepId);

    if (result.passed) showToast("Nice — that passed.", "success");
  } catch (e) {
    showToast(e.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Check my work";
  }
});

// ---------------- Mentor hints ----------------
$("btn-toggle-mentor").addEventListener("click", () => {
  $("mentor-panel").classList.toggle("hidden");
});

$("btn-ask-mentor").addEventListener("click", async () => {
  const question = $("mentor-question").value.trim();
  if (!question) return showToast("Type your question first.", "error");

  const btn = $("btn-ask-mentor");
  btn.disabled = true;
  btn.textContent = "Thinking…";

  try {
    const code = editor.getValue();
    const { hint } = await postJSON(`/api/steps/${currentStepId}/hint`, { question, code });
    $("mentor-response").textContent = hint;
  } catch (e) {
    showToast(e.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Ask";
  }
});

// ---------------- Init ----------------
async function init() {
  try {
    curriculum = await getJSON("/api/curriculum");
    progress = await getJSON("/api/progress");
    buildStepLookup();
    renderNav();
  } catch (e) {
    showToast(e.message, "error");
  }
}

initEditor();
init();
