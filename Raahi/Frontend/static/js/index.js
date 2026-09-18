/* ==========================================
   CORE JS UTILITIES
   ========================================== */

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

/* ==========================================
   TOAST NOTIFICATION SYSTEM
   ========================================== */
function showToast(title, message, type = 'info', duration = 4000) {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const icons = {
    success: 'fa-solid fa-circle-check',
    error: 'fa-solid fa-circle-exclamation',
    warning: 'fa-solid fa-triangle-exclamation',
    info: 'fa-solid fa-circle-info'
  };

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div class="toast-icon"><i class="${icons[type] || icons.info}"></i></div>
    <div class="toast-content">
      <span class="toast-title">${title}</span>
      ${message ? `<span class="toast-message">${message}</span>` : ''}
    </div>
    <button class="toast-close" onclick="dismissToast(this.parentElement)" aria-label="Close">
      <i class="fa-solid fa-xmark"></i>
    </button>
  `;

  container.appendChild(toast);

  setTimeout(() => dismissToast(toast), duration);
}

function dismissToast(toast) {
  if (!toast || toast.classList.contains('toast-out')) return;
  toast.classList.add('toast-out');
  setTimeout(() => toast.remove(), 300);
}

/* ==========================================
   ENTER KEY HANDLER FOR CHAT INPUT
   ========================================== */
document.getElementById("userInput")?.addEventListener("keydown", function (e) {
  if (e.key === "Enter") {
    sendMessage();
  }
});

/* ==========================================
   PLACE INPUT SYNC TO SESSION
   ========================================== */
const placeInput = document.getElementById("placeInput");
const discoverBtn = document.getElementById("discoverBtn");

if (placeInput && discoverBtn) {
  placeInput.addEventListener("input", () => {
    const place = placeInput.value.trim();
    fetch("/set-place/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken")
      },
      body: JSON.stringify({ place })
    });
    discoverBtn.innerHTML = place
      ? `<i class="fa-solid fa-calendar-plus"></i> Discover in ${place}`
      : `<i class="fa-solid fa-calendar-plus"></i> Generate Smart Itinerary Plan`;
  });
}
