/* ==========================================
   CHATBOT — POLISHED
   ========================================== */

function sendMessage() {
  const userInput = document.getElementById("userInput");
  const message = userInput.value.trim();
  if (!message) return;

  const chatMessages = document.getElementById("chatMessages");

  /* User bubble */
  const userDiv = document.createElement("div");
  userDiv.className = "message user-bubble";
  userDiv.innerHTML = `<p>${escapeHTML(message)}</p>`;
  chatMessages.appendChild(userDiv);
  userInput.value = "";
  chatMessages.scrollTop = chatMessages.scrollHeight;

  /* Typing indicator */
  const typing = document.createElement("div");
  typing.className = "typing-indicator";
  typing.id = "typingIndicator";
  typing.innerHTML = `
    <div class="bot-avatar-small"><i class="fa-solid fa-robot"></i></div>
    <div class="typing-dots"><span></span><span></span><span></span></div>
  `;
  chatMessages.appendChild(typing);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  fetch("/chat/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken")
    },
    body: JSON.stringify({ message: message })
  })
    .then(res => res.json())
    .then(data => {
      removeTyping();
      const botDiv = document.createElement("div");
      botDiv.className = "message bot-bubble";
      const reply = data.reply || "No reply received.";
      botDiv.innerHTML = `
        <div class="bot-avatar-small"><i class="fa-solid fa-robot"></i></div>
        <p>${escapeHTML(reply)}</p>
      `;
      chatMessages.appendChild(botDiv);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    })
    .catch(() => {
      removeTyping();
      const errorDiv = document.createElement("div");
      errorDiv.className = "message bot-bubble";
      errorDiv.innerHTML = `
        <div class="bot-avatar-small"><i class="fa-solid fa-robot"></i></div>
        <p style="color: #ef4444;">Network error. Please try again.</p>
      `;
      chatMessages.appendChild(errorDiv);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    });
}

function removeTyping() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

function escapeHTML(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function requestItinerary() {
  fetch("/get-place/", {
    headers: { "X-CSRFToken": getCookie("csrftoken") }
  })
    .then(res => res.json())
    .then(data => {
      if (!data.place) {
        showToast("No destination", "Search a destination on the map first.", "warning");
        return;
      }
      const input = document.getElementById("userInput");
      input.value = `Create a detailed day-by-day travel itinerary for ${data.place}. Include attractions, restaurants, and tips.`;
      sendMessage();
    })
    .catch(() => {
      showToast("Error", "Could not fetch place data. Try again.", "error");
    });
}

function sendChipPrompt(prompt) {
  if (!prompt) return;
  const input = document.getElementById("userInput");
  input.value = prompt;
  sendMessage();
}
