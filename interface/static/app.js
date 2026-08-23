// Estado global de la aplicación
let activeSessionId = localStorage.getItem("cuequi_active_session") || null;
const AVATAR_URL = "/static/uploads/avatar.png";

const viewport = document.getElementById("messages-viewport");
const inputField = document.getElementById("user-input");
const sendButton = document.getElementById("btn-send");
const sessionsList = document.getElementById("sessions-list");

// ================= INICIALIZACIÓN =================
async function initApp() {
  await loadSystemStats();
  await loadSessionsList();
  
  if (!activeSessionId) {
    await startNewChat();
  } else {
    await loadSessionHistory(activeSessionId);
  }
}

// ================= GESTIÓN DE SESIONES / HISTORIAL =================
async function loadSessionsList() {
  try {
    const res = await fetch("/api/sessions");
    if (res.ok) {
      const sessions = await res.json();
      renderSessionsSidebar(sessions);
    }
  } catch (e) {
    sessionsList.innerHTML = `<div class="session-empty">Error al cargar historial</div>`;
  }
}

function renderSessionsSidebar(sessions) {
  if (!sessions || sessions.length === 0) {
    sessionsList.innerHTML = `<div class="session-empty">No hay conversaciones previas</div>`;
    return;
  }

  sessionsList.innerHTML = sessions.map(s => {
    const isActive = s.id === activeSessionId ? "active" : "";
    return `
      <div class="session-item ${isActive}" onclick="switchSession('${s.id}')">
        <span class="session-title-text" title="${escapeHtml(s.title)}">💬 ${escapeHtml(s.title)}</span>
        <button class="btn-delete-session" onclick="deleteSession('${s.id}', event)" title="Eliminar conversación">🗑️</button>
      </div>
    `;
  }).join("");
}

async function startNewChat() {
  try {
    const res = await fetch("/api/sessions/new", { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      activeSessionId = data.session_id;
      localStorage.setItem("cuequi_active_session", activeSessionId);
      await loadSessionsList();
      renderWelcomeMessage();
    }
  } catch (e) {
    console.error("Error creando nueva sesión:", e);
  }
}

async function switchSession(sessionId) {
  if (activeSessionId === sessionId) return;
  activeSessionId = sessionId;
  localStorage.setItem("cuequi_active_session", activeSessionId);
  await loadSessionsList();
  await loadSessionHistory(sessionId);
}

async function loadSessionHistory(sessionId) {
  viewport.innerHTML = "";
  try {
    const res = await fetch(`/api/sessions/${sessionId}`);
    if (res.ok) {
      const session = await res.json();
      const messages = session.messages || [];
      if (messages.length === 0) {
        renderWelcomeMessage();
      } else {
        messages.forEach(msg => {
          if (msg.role === "user") {
            appendUserMessage(msg.content);
          } else {
            appendBotMessage(msg.content, msg.metadata?.sources || [], msg.metadata?.sources_meta || []);
          }
        });
      }
    } else {
      await startNewChat();
    }
  } catch (e) {
    renderWelcomeMessage();
  }
}

async function deleteSession(sessionId, event) {
  event.stopPropagation();
  if (confirm("¿Deseas eliminar esta conversación?")) {
    await fetch(`/api/sessions/${sessionId}`, { method: "DELETE" });
    if (activeSessionId === sessionId) {
      activeSessionId = null;
      localStorage.removeItem("cuequi_active_session");
      await startNewChat();
    } else {
      await loadSessionsList();
    }
  }
}

function renderWelcomeMessage() {
  viewport.innerHTML = "";
  const row = document.createElement("div");
  row.className = "message-row bot-row welcome-msg";
  const avatarHtml = `<img src="${AVATAR_URL}" alt="Cuequi" onerror="this.outerHTML='CQ'">`;

  row.innerHTML = `
    <div class="msg-avatar">${avatarHtml}</div>
    <div class="msg-content-wrapper">
      <div class="msg-bubble">
        <p>hola ;)</p>
      </div>
    </div>
  `;
  viewport.appendChild(row);
  scrollToBottom();
}

// ================= ESTADÍSTICAS DEL SISTEMA =================
async function loadSystemStats() {
  try {
    const res = await fetch("/api/stats");
    if (res.ok) {
      const data = await res.json();
      document.getElementById("stat-texts").innerText = data.total_texts;
      document.getElementById("stat-vectors").innerText = data.total_vectors;
      document.getElementById("stat-model").innerText = data.active_model || "GROQ";
    }
  } catch (err) {
    console.warn("No se pudieron cargar las estadísticas:", err);
  }
}

// ================= INTERACCIÓN DEL CHAT (STREAMING) =================
inputField.addEventListener("input", () => {
  inputField.style.height = "auto";
  inputField.style.height = Math.min(inputField.scrollHeight, 120) + "px";
});

function handleKeyDown(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    document.getElementById("chat-form").requestSubmit();
  }
}

async function handleFormSubmit(e) {
  e.preventDefault();
  const text = inputField.value.trim();
  if (!text) return;

  appendUserMessage(text);
  inputField.value = "";
  inputField.style.height = "auto";
  inputField.disabled = true;
  sendButton.disabled = true;

  const botRow = createBotMessageRow();
  viewport.appendChild(botRow);
  scrollToBottom();

  const bubble = botRow.querySelector(".msg-bubble");
  const contentWrapper = botRow.querySelector(".msg-content-wrapper");

  let fullResponseText = "";
  let retrievedDocs = [];
  let sourcesMeta = [];
  let isFirstChunk = true;

  try {
    const response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        session_id: activeSessionId
      })
    });

    if (!response.ok) {
      throw new Error(`Error del servidor (${response.status})`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const jsonStr = line.replace("data: ", "").trim();
        if (!jsonStr) continue;

        try {
          const event = JSON.parse(jsonStr);
          
          if (event.type === "metadata") {
            retrievedDocs = event.retrieved_documents || [];
            sourcesMeta = event.sources_metadata || [];
          } else if (event.type === "chunk") {
            if (isFirstChunk) {
              bubble.innerHTML = "";
              isFirstChunk = false;
            }
            fullResponseText += event.content;
            renderMarkdownText(bubble, fullResponseText);
            scrollToBottom();
          }
        } catch (parseErr) {
          console.error("Error parseando chunk:", parseErr);
        }
      }
    }

    // Actualizar sidebar para reflejar el nuevo título de conversación
    loadSessionsList();

  } catch (err) {
    bubble.innerHTML = `<p style="color: #f87171;">⚠️ Error al procesar: ${escapeHtml(err.message)}</p>`;
  } finally {
    inputField.disabled = false;
    sendButton.disabled = false;
    inputField.focus();
    scrollToBottom();
  }
}

function appendUserMessage(text) {
  const row = document.createElement("div");
  row.className = "message-row user-row";
  row.innerHTML = `
    <div class="msg-avatar">Tú</div>
    <div class="msg-content-wrapper">
      <div class="msg-bubble">
        <p>${escapeHtml(text)}</p>
      </div>
    </div>
  `;
  viewport.appendChild(row);
  scrollToBottom();
}

function createBotMessageRow() {
  const row = document.createElement("div");
  row.className = "message-row bot-row";
  const avatarHtml = `<img src="${AVATAR_URL}" alt="Cuequi" onerror="this.outerHTML='CQ'">`;

  row.innerHTML = `
    <div class="msg-avatar">${avatarHtml}</div>
    <div class="msg-content-wrapper">
      <div class="msg-bubble">
        <div class="typing-indicator">
          <div class="dot"></div>
          <div class="dot"></div>
          <div class="dot"></div>
        </div>
      </div>
    </div>
  `;
  return row;
}

function appendBotMessage(text) {
  const row = document.createElement("div");
  row.className = "message-row bot-row";
  const avatarHtml = `<img src="${AVATAR_URL}" alt="Cuequi" onerror="this.outerHTML='CQ'">`;

  const paragraphs = text
    .split("\n\n")
    .map(p => `<p>${escapeHtml(p).replace(/\n/g, "<br>")}</p>`)
    .join("");

  row.innerHTML = `
    <div class="msg-avatar">${avatarHtml}</div>
    <div class="msg-content-wrapper">
      <div class="msg-bubble">
        ${paragraphs}
      </div>
    </div>
  `;
  viewport.appendChild(row);
  scrollToBottom();
}

function renderMarkdownText(container, text) {
  const paragraphs = text
    .split("\n\n")
    .map(p => `<p>${escapeHtml(p).replace(/\n/g, "<br>")}</p>`)
    .join("");
  container.innerHTML = paragraphs;
}

function scrollToBottom() {
  viewport.scrollTop = viewport.scrollHeight;
}

function escapeHtml(string) {
  const entityMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  };
  return String(string).replace(/[&<>"']/g, s => entityMap[s]);
}

// Iniciar aplicación al cargar la página
window.addEventListener("DOMContentLoaded", initApp);
