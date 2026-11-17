const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const messages = document.getElementById("messages");
const welcome = document.getElementById("welcome");
const sendBtn = document.getElementById("sendBtn");
let sessionId = localStorage.getItem("nova_session_id");

function addMessage(role, text) {
  welcome.style.display = "none";
  const row = document.createElement("div");
  row.className = `message ${role}`;
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "◉" : "✦";
  const content = document.createElement("div");
  content.className = "bubble";
  content.textContent = text;
  row.appendChild(avatar);
  row.appendChild(content);
  messages.appendChild(row);
  document.getElementById("chatArea").scrollTop = document.getElementById("chatArea").scrollHeight;
}

function addTyping() {
  const row = document.createElement("div");
  row.className = "message bot";
  row.id = "typing";
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = "✦";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = "Nova is thinking...";
  row.append(avatar, bubble);
  messages.appendChild(row);
  document.getElementById("chatArea").scrollTop = document.getElementById("chatArea").scrollHeight;
}

async function sendMessage(text) {
  const message = text.trim();
  if (!message) return;
  addMessage("user", message);
  input.value = "";
  input.style.height = "auto";
  sendBtn.disabled = true;
  addTyping();

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message, session_id: sessionId})
    });
    if (!response.ok) throw new Error("Request failed");
    const data = await response.json();
    sessionId = data.session_id;
    localStorage.setItem("nova_session_id", sessionId);
    document.getElementById("typing")?.remove();
    addMessage("bot", data.reply);
  } catch (error) {
    document.getElementById("typing")?.remove();
    addMessage("bot", "I couldn't connect to the server. Make sure the FastAPI app is running, then try again.");
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", event => {
  event.preventDefault();
  sendMessage(input.value);
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 140) + "px";
});

document.querySelectorAll("[data-message]").forEach(button => {
  button.addEventListener("click", () => sendMessage(button.dataset.message));
});

document.getElementById("newChat").addEventListener("click", resetChat);
document.getElementById("clearChat").addEventListener("click", resetChat);

async function resetChat() {
  if (sessionId) {
    fetch("/api/reset", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message: "", session_id: sessionId})
    }).catch(() => {});
  }
  sessionId = null;
  localStorage.removeItem("nova_session_id");
  messages.innerHTML = "";
  welcome.style.display = "block";
  input.focus();
}
