const form = document.getElementById("ask-form");
const queryInput = document.getElementById("query-input");
const topKInput = document.getElementById("top-k-input");
const submitButton = document.getElementById("submit-button");
const reloadButton = document.getElementById("reload-button");
const answerList = document.getElementById("answer-list");
const contextList = document.getElementById("context-list");
const libraryCaption = document.getElementById("library-caption");
const libraryMeta = document.getElementById("library-meta");
const libraryList = document.getElementById("library-list");
const skippedMeta = document.getElementById("skipped-meta");
const statusPill = document.getElementById("status-pill");
const errorBox = document.getElementById("error-box");

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "请求失败");
  }
  return payload;
}

function setLoading(loading) {
  submitButton.disabled = loading;
  submitButton.textContent = loading ? "检索中..." : "开始检索";
  if (loading) {
    statusPill.textContent = "正在检索";
  }
  statusPill.classList.toggle("loading", loading);
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}

function clearError() {
  errorBox.textContent = "";
  errorBox.classList.add("hidden");
}

function renderAnswers(lines) {
  if (!lines.length) {
    answerList.innerHTML = "<li>没有生成回答。</li>";
    return;
  }

  // Use marked.js to render markdown if available
  if (typeof marked !== "undefined") {
    const markdown = lines.join("\n\n");
    answerList.innerHTML = `<div class="markdown-body">${marked.parse(markdown)}</div>`;
  } else {
    answerList.innerHTML = lines.map((line) => `<li>${escapeHtml(line)}</li>`).join("");
  }
}

function renderContexts(hits) {
  if (!hits.length) {
    contextList.innerHTML = `
      <article class="context-card muted">
        <p>没有命中上下文。</p>
      </article>
    `;
    return;
  }

  contextList.innerHTML = hits
    .map(
      (hit) => `
        <article class="context-card">
          <div class="context-head">
            <strong>${escapeHtml(hit.source)}</strong>
            <span class="score">
              Score ${Number(hit.score).toFixed(3)}
              <span class="score-detail" title="Vector / BM25 / Title">
                (Vec: ${Number(hit.retrieve_score).toFixed(2)}, BM25: ${Number(hit.lexical_score).toFixed(2)})
              </span>
            </span>
          </div>
          <p>${escapeHtml(hit.text)}</p>
        </article>
      `
    )
    .join("");
}

function renderLibrary(payload) {
  libraryMeta.textContent = `已入库 ${payload.documents} 个文档，切分为 ${payload.chunks} 个 chunk。支持格式：${payload.supported_formats.join(", ")}。Embedding：${payload.embedding_backend}。Reranker：${payload.reranker_backend}。检索链路：${payload.retrieval_strategy} -> ${payload.rerank_strategy}`;

  if (!payload.files.length) {
    libraryList.innerHTML = `
      <article class="context-card muted">
        <p>文档库里还没有可入库的文件。</p>
      </article>
    `;
  } else {
    libraryList.innerHTML = payload.files
      .map(
        (item) => `
          <article class="library-item">
            <strong>${escapeHtml(item.source)}</strong>
            <p>${escapeHtml(item.title)}</p>
            <p>类型：${escapeHtml(item.file_type)} | 文本长度：${escapeHtml(item.chars)}</p>
          </article>
        `
      )
      .join("");
  }

  if (payload.skipped.length) {
    skippedMeta.textContent = `跳过 ${payload.skipped.length} 个文件：${payload.skipped
      .map((item) => `${item.source} (${item.error})`)
      .join("；")}`;
    skippedMeta.classList.remove("hidden");
  } else {
    skippedMeta.textContent = "";
    skippedMeta.classList.add("hidden");
  }
}

async function loadLibrary() {
  const payload = await fetchJson("/api/library");
  renderLibrary(payload);
  return payload;
}

async function askQuestion(query, topK) {
  setLoading(true);
  clearError();

  try {
    const payload = await fetchJson("/api/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        top_k: Number(topK),
      }),
    });

    renderAnswers(payload.answer_lines || []);
    renderContexts(payload.hits || []);
    statusPill.textContent = `命中 ${payload.hits?.length || 0} 条上下文`;
  } catch (error) {
    renderAnswers([]);
    renderContexts([]);
    showError(error.message || "发生未知错误");
    statusPill.textContent = "请求失败";
  } finally {
    setLoading(false);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = queryInput.value.trim();
  const topK = topKInput.value.trim() || "3";

  if (!query) {
    showError("请输入问题。");
    return;
  }

  await askQuestion(query, topK);
});

reloadButton.addEventListener("click", async () => {
  reloadButton.disabled = true;
  clearError();
  try {
    const payload = await fetchJson("/api/reload", { method: "POST" });
    renderLibrary(payload);
    statusPill.textContent = payload.message || "重新入库完成";
  } catch (error) {
    showError(error.message || "重新入库失败");
    statusPill.textContent = "重新入库失败";
  } finally {
    reloadButton.disabled = false;
  }
});

async function bootstrap() {
  try {
    await loadLibrary();
  } catch (error) {
    showError(error.message || "读取文档库失败");
  }

  const initialQuery = queryInput.value.trim();
  if (initialQuery) {
    await askQuestion(initialQuery, topKInput.value.trim() || "3");
  }
}

bootstrap();
