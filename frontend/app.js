const STORAGE_KEY = "school-chat-history-v1";
const GREETING = "Mình sẵn sàng tra cứu lịch học, lịch thi, phòng học và sinh viên từ database.";

const form = document.querySelector("#chatForm");
const input = document.querySelector("#messageInput");
const sendButton = document.querySelector("#sendButton");
const messages = document.querySelector("#messages");
const historyList = document.querySelector("#historyList");
const newChatButton = document.querySelector("#newChatButton");
const chatTitle = document.querySelector("#chatTitle");

let sessions = loadSessions();
let currentSessionId = sessions[0]?.id || createSession(false).id;

renderAll();

function loadSessions() {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveSessions() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions.slice(0, 40)));
}

function createId() {
  if (window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }
  return `chat-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function createSession(makeActive = true) {
  const session = {
    id: createId(),
    title: "Cuộc trò chuyện mới",
    updatedAt: Date.now(),
    messages: [{ role: "assistant", text: GREETING }],
  };
  sessions.unshift(session);
  if (makeActive) {
    currentSessionId = session.id;
  }
  saveSessions();
  return session;
}

function getCurrentSession() {
  let session = sessions.find((item) => item.id === currentSessionId);
  if (!session) {
    session = createSession(true);
  }
  return session;
}

function updateSession(session) {
  session.updatedAt = Date.now();
  sessions = [session, ...sessions.filter((item) => item.id !== session.id)];
  currentSessionId = session.id;
  saveSessions();
}

function renderAll() {
  renderHistory();
  renderMessages();
}

function renderHistory() {
  historyList.innerHTML = "";

  if (sessions.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty-history";
    empty.textContent = "Chưa có lịch sử.";
    historyList.append(empty);
    return;
  }

  sessions.forEach((session) => {
    const item = document.createElement("div");
    item.className = `history-item${session.id === currentSessionId ? " active" : ""}`;

    const titleButton = document.createElement("button");
    titleButton.className = "history-title";
    titleButton.type = "button";
    titleButton.textContent = session.title;
    titleButton.title = session.title;
    titleButton.addEventListener("click", () => {
      currentSessionId = session.id;
      renderAll();
    });

    const deleteButton = document.createElement("button");
    deleteButton.className = "delete-chat";
    deleteButton.type = "button";
    deleteButton.title = "Xóa chat";
    deleteButton.setAttribute("aria-label", "Xóa chat");
    deleteButton.textContent = "×";
    deleteButton.addEventListener("click", () => deleteSession(session.id));

    item.append(titleButton, deleteButton);
    historyList.append(item);
  });
}

function renderMessages() {
  const session = getCurrentSession();
  messages.innerHTML = "";
  chatTitle.textContent = session.title;
  session.messages.forEach((message) => appendMessage(message.role, message.text, false));
  messages.scrollTop = messages.scrollHeight;
}

function appendMessage(role, text, persist = true) {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "Bạn" : "AI";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  bubble.append(paragraph);

  article.append(avatar, bubble);
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;

  if (persist) {
    const session = getCurrentSession();
    session.messages.push({ role, text });
    if (role === "user" && session.title === "Cuộc trò chuyện mới") {
      session.title = makeTitle(text);
    }
    updateSession(session);
    renderHistory();
    chatTitle.textContent = session.title;
  }

  return article;
}

function makeTitle(text) {
  const cleaned = text.replace(/\s+/g, " ").trim();
  return cleaned.length > 44 ? `${cleaned.slice(0, 44)}...` : cleaned || "Cuộc trò chuyện mới";
}

function deleteSession(id) {
  sessions = sessions.filter((session) => session.id !== id);
  if (sessions.length === 0) {
    const session = createSession(false);
    currentSessionId = session.id;
  } else if (currentSessionId === id) {
    currentSessionId = sessions[0].id;
  }
  saveSessions();
  renderAll();
}

async function sendMessage(message) {
  appendMessage("user", message);
  const pending = appendMessage("assistant", "Đang suy nghĩ...");
  const session = getCurrentSession();

  const statusMessages = [
    "Đang phân tích câu hỏi...",
    "Đang chọn tool phù hợp...",
    "Đang truy vấn database...",
    "Đang tổng hợp câu trả lời...",
  ];
  let statusIndex = 0;
  const statusTimer = window.setInterval(() => {
    statusIndex = (statusIndex + 1) % statusMessages.length;
    pending.querySelector("p").textContent = statusMessages[statusIndex];
  }, 900);

  sendButton.disabled = true;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Request failed");
    }
    pending.querySelector("p").textContent = data.answer;
    session.messages[session.messages.length - 1] = { role: "assistant", text: data.answer };
    updateSession(session);
  } catch (error) {
    pending.querySelector("p").textContent = error.message;
    pending.querySelector("p").classList.add("error");
    session.messages[session.messages.length - 1] = { role: "assistant", text: error.message };
    updateSession(session);
  } finally {
    window.clearInterval(statusTimer);
    sendButton.disabled = false;
    input.focus();
    messages.scrollTop = messages.scrollHeight;
  }
}

function resizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 170)}px`;
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  resizeInput();
  sendMessage(message);
});

input.addEventListener("input", resizeInput);
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

newChatButton.addEventListener("click", () => {
  createSession(true);
  renderAll();
  input.focus();
});
