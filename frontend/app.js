let API_BASE = ""; // will be set from config (config.local.json/config.example.json)

const uploadForm = document.getElementById("upload-form");
const pdfInput = document.getElementById("pdf-file");
const fileNameEl = document.getElementById("file-name");
const questionCountInput = document.getElementById("question-count");
const countMaxEl = document.getElementById("count-max");
const statusEl = document.getElementById("status");
const progressLabel = document.getElementById("progress-label");
const progressFill = document.getElementById("progress-fill");
const quizSection = document.getElementById("quiz");
const progressEl = document.getElementById("progress");
const questionContainer = document.getElementById("question-container");
const feedbackEl = document.getElementById("feedback");

const quizState = {
  quizId: null,
  questions: [],
  attempts: {}, // questionId -> attempt count
  summaryShown: false,
};

async function loadConfig() {
  const candidates = ["config.local.json", "config.example.json"];
  for (const file of candidates) {
    try {
      const res = await fetch(file, { cache: "no-store" });
      if (!res.ok) continue;
      const cfg = await res.json();
      if (cfg.BACKEND_URL) {
        API_BASE = cfg.BACKEND_URL.replace(/\/$/, "");
        return;
      }
    } catch (err) {
      continue;
    }
  }
  API_BASE = "";
}

async function init() {
  await loadConfig();
  console.log("Using API_BASE:", API_BASE || "(same origin)");
  if (!API_BASE) {
    statusEl.textContent = "No backend URL configured; using same origin.";
  }
  setProgress(0, "Idle");
  await loadBackendConfig();
}

init().catch((err) => {
  console.error("Init error:", err);
  statusEl.textContent = "Failed to initialize frontend.";
  setProgress(0, "Idle");
});

async function loadBackendConfig() {
  try {
    const res = await fetch(`${API_BASE || ""}/config`);
    if (!res.ok) throw new Error("Failed to load backend config.");
    const cfg = await res.json();
    const maxQ = cfg.max_questions || 6;
    questionCountInput.max = maxQ;
    questionCountInput.value = Math.min(Number(questionCountInput.value) || maxQ, maxQ);
    countMaxEl.textContent = `Max ${maxQ}`;
  } catch (err) {
    console.warn("Could not load backend config; using defaults.");
    const maxQ = Number(questionCountInput.value) || 6;
    questionCountInput.max = maxQ;
    countMaxEl.textContent = "";
  }
}

pdfInput.addEventListener("change", () => {
  if (pdfInput.files && pdfInput.files[0]) {
    fileNameEl.textContent = pdfInput.files[0].name;
  } else {
    fileNameEl.textContent = "No file chosen";
  }
});

uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  feedbackEl.textContent = "";
  statusEl.textContent = "";

  const file = pdfInput.files[0];
  if (!file) {
    statusEl.textContent = "Please choose a PDF.";
    return;
  }

  try {
    statusEl.textContent = "";
    setProgress(10, "Preparing upload…");
    const formData = new FormData();
    formData.append("file", file);
    const desired = Number(questionCountInput.value) || 1;
    formData.append("num_questions", desired);

    const data = await uploadWithProgress(formData);
    quizState.quizId = data.quiz_id;
    quizState.attempts = {};
    quizState.summaryShown = false;
    await loadQuiz();
    setProgress(100, "Quiz generated.");
    quizSection.classList.remove("hidden");
  } catch (err) {
    console.error(err);
    statusEl.textContent = err.message || "Something went wrong.";
    setProgress(0, "Idle");
  }
});

async function uploadWithProgress(formData) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const target = `${API_BASE || ""}/upload-pdf`;
    console.log("Uploading to:", target);
    xhr.open("POST", target);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const pct = Math.min(80, Math.round((event.loaded / event.total) * 70) + 10);
        setProgress(pct, "Uploading PDF…");
      } else {
        setProgress(40, "Uploading PDF…");
      }
    };

    xhr.onloadstart = () => setProgress(10, "Starting upload…");
    xhr.onload = () => {
      // Move to generating phase after upload
      setProgress(85, "Generating questions…");
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const json = JSON.parse(xhr.responseText);
          resolve(json);
        } catch (err) {
          reject(new Error("Invalid server response."));
        }
      } else {
        let detail = "Upload failed.";
        try {
          const resp = JSON.parse(xhr.responseText);
          detail = resp.detail || detail;
        } catch (_) {}
        reject(new Error(detail));
      }
    };
    xhr.onerror = () => reject(new Error("Network error during upload (check API_BASE and backend)."));
    xhr.onabort = () => reject(new Error("Upload aborted."));
    xhr.ontimeout = () => reject(new Error("Upload timed out."));
    xhr.send(formData);
  });
}

async function loadQuiz() {
  const res = await fetch(`${API_BASE}/quiz/${quizState.quizId}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to load quiz.");
  }
  const data = await res.json();
  quizState.questions = data.questions;
  renderQuiz(data.completed);
}

function renderQuiz(completed) {
  const total = quizState.questions.length;
  const correct = quizState.questions.filter((q) => q.is_correct).length;
  if (completed || correct === total) {
    progressEl.textContent = `All questions complete (${total}/${total})`;
  } else {
    const current = Math.min(correct + 1, total);
    progressEl.textContent = `Question ${current} of ${total}`;
  }

  if (completed || correct === total) {
    questionContainer.innerHTML = `<p class="success">🎉 All questions answered correctly!</p>`;
    if (!quizState.summaryShown) {
      renderSummary();
      quizState.summaryShown = true;
    }
    return;
  }

  const nextQuestion = quizState.questions.find((q) => !q.is_correct);
  if (!nextQuestion) {
    questionContainer.innerHTML = `<p class="success">🎉 All questions answered correctly!</p>`;
    return;
  }

  const optionsHtml = nextQuestion.options
    .map(
      (opt, idx) => `
      <label class="option">
        <input type="radio" name="option" value="${idx}" />
        <span class="option-label">${String.fromCharCode(65 + idx)}</span>
        <span>${opt}</span>
      </label>`
    )
    .join("");

  questionContainer.innerHTML = `
    <div class="question-block">
      <div class="question-meta">
        <div class="pill">MCQ</div>
        <div class="pill soft">${correct}/${total} correct</div>
      </div>
      <h3>${nextQuestion.question}</h3>
      <div class="options">${optionsHtml}</div>
      <button id="submit-answer" class="primary">Submit</button>
    </div>
  `;

  document
    .getElementById("submit-answer")
    .addEventListener("click", () => submitAnswer(nextQuestion.id));
}

async function submitAnswer(questionId) {
  feedbackEl.textContent = "";
  const selected = document.querySelector('input[name="option"]:checked');
  if (!selected) {
    feedbackEl.textContent = "Please choose an option.";
    return;
  }

  const payload = {
    question_id: questionId,
    selected_option_index: Number(selected.value),
  };

  try {
    const res = await fetch(`${API_BASE}/quiz/${quizState.quizId}/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to submit answer.");
    }
    const data = await res.json();

    quizState.attempts[questionId] = (quizState.attempts[questionId] || 0) + 1;

    if (data.quiz_completed) {
      feedbackEl.textContent = "";
    } else if (data.correct) {
      feedbackEl.innerHTML = `<div class="success">Correct! ${data.explanation || ""}</div>`;
    } else {
      feedbackEl.innerHTML = `<div class="hint">Try again. Hint: ${data.hint || ""}</div>`;
    }

    await loadQuiz();
  } catch (err) {
    console.error(err);
    feedbackEl.textContent = err.message || "Failed to submit answer.";
  }
}

function setProgress(percent, label) {
  progressFill.style.width = `${percent}%`;
  progressLabel.textContent = label;
}

function renderSummary() {
  const total = quizState.questions.length;
  const attempts = Object.values(quizState.attempts).reduce((a, b) => a + b, 0);
  const firstTryCorrect = quizState.questions.filter(
    (q) => quizState.attempts[q.id] === 1
  ).length;
  const avgAttempts = total ? (attempts / total).toFixed(2) : "0";

  feedbackEl.innerHTML = `
    <div class="summary-card">
      <h4>Performance Summary</h4>
      <div class="summary-grid">
        <div><span class="summary-label">Questions:</span> ${total}</div>
        <div><span class="summary-label">Total attempts:</span> ${attempts}</div>
        <div><span class="summary-label">Avg attempts/question:</span> ${avgAttempts}</div>
        <div><span class="summary-label">First-try correct:</span> ${firstTryCorrect}/${total}</div>
      </div>
    </div>
  `;
}
