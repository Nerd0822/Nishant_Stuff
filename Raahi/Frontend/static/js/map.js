/* ==========================================
   COOKIE HELPER (inlined from index.js)
   ========================================== */
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

/* ==========================================
   HTML ESCAPE (inlined from chatbot.js)
   ========================================== */
function escapeHTML(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

/* ==========================================
   ALPINE TOAST HELPER (replaces showToast)
   ========================================== */
function showToast(title, message, type = 'info', duration = 4000) {
  const icons = {
    success: 'fa-solid fa-circle-check',
    error: 'fa-solid fa-circle-exclamation',
    warning: 'fa-solid fa-triangle-exclamation',
    info: 'fa-solid fa-circle-info'
  };
  if (window.__toasts) {
    window.__toasts.push({
      type: type,
      icon: icons[type] || icons.info,
      title: title,
      message: message || '',
      visible: true,
    });
    setTimeout(() => {
      const t = window.__toasts[window.__toasts.length - 1];
      if (t) t.visible = false;
    }, duration);
  }
}

var map = L.map('map').setView([28.6139, 77.2090], 5);

// Structural Canvas Layer Render Definitions
var satelliteOverlay = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
  maxZoom: 18,
  opacity: 1,
  attribution: 'Tiles &copy; Esri &mdash; Source: Esri, Earthstar Geographics'
}).addTo(map);

var baseLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 20,
  opacity: 0.4,
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Invalidate layout metrics to force dynamic tile re-calculation against grid boundaries
setTimeout(() => {
  map.invalidateSize();
}, 400);

let userMarker, userCircle;
let startMarker, endMarker, routeControl;
let lastSearchedPlace = "";
let lastSearchedLat = "";
let lastSearchedLon = "";

const userIcon = L.icon({
  iconUrl: 'https://cdn-icons-png.flaticon.com/512/684/684908.png',
  iconSize: [25, 25],
  iconAnchor: [12, 12]
});

// Structural high performance location tracking runtime
navigator.geolocation.watchPosition(position => {
  const lat = position.coords.latitude;
  const lon = position.coords.longitude;
  const userLatLng = [lat, lon];

  if (!userMarker) {
    userMarker = L.marker(userLatLng, { icon: userIcon }).addTo(map).bindPopup("You are here");
    userCircle = L.circle(userLatLng, {
      radius: 12,
      color: '#0ea5e9',
      fillColor: '#0ea5e9',
      fillOpacity: 0.25
    }).addTo(map);
  } else {
    userMarker.setLatLng(userLatLng);
    userCircle.setLatLng(userLatLng);
  }
}, () => {
  console.log("Active tracking fallback state engaged.");
}, {
  enableHighAccuracy: true,
  maximumAge: 10000,
  timeout: 10000
});

var satelliteAdded = true;
map.on('zoomend', function () {
  var currentZoom = map.getZoom();

  if (currentZoom > 18 && satelliteAdded) {
    map.removeLayer(satelliteOverlay);
    satelliteAdded = false;
  } else if (currentZoom <= 18 && !satelliteAdded) {
    map.addLayer(satelliteOverlay);
    map.removeLayer(baseLayer);
    map.addLayer(baseLayer);
    satelliteAdded = true;
  }
});



function searchPlace() {
  const place = document.getElementById('placeInput').value.trim();
  if (!place) return alert("Please provide a coordinate title or city handle.");

  lastSearchedPlace = place;

  fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(place)}`)
    .then(res => res.json())
    .then(data => {
      if (data.length > 0) {
        const lat = parseFloat(data[0].lat);
        const lon = parseFloat(data[0].lon);
        lastSearchedLat = lat;
        lastSearchedLon = lon;

        map.setView([lat, lon], 13);

        if (endMarker) {
          endMarker.setLatLng([lat, lon]);
        } else {
          endMarker = L.marker([lat, lon]).addTo(map);
        }

        const popupHtml = `
          <div style="text-align:center;">
            <strong>${escapeHTML(place)}</strong><br>
            <button hx-post="/save-place/"
                    hx-vals='${JSON.stringify({name: place, lat, lon})}'
                    hx-target="#toastContainer"
                    hx-swap="beforeend"
                    style="margin-top:8px;padding:6px 14px;background:linear-gradient(135deg,#ff6b35,#ff4b4b);color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:0.85rem;font-weight:600;">
              🔖 Save Place
            </button>
          </div>`;
        endMarker.bindPopup(popupHtml).openPopup();

        document.getElementById("directionsSection").style.display = "flex";

        const saveBtn = document.getElementById("savePlaceBtn");
        saveBtn.disabled = false;
        saveBtn.style.opacity = "1";
        saveBtn.style.pointerEvents = "auto";
        saveBtn.title = "Save this destination";

        if (startMarker) {
          showRoute();
        }
      }
    });
}


function saveCurrentPlace() {
  if (!lastSearchedPlace) {
    showToast("No destination", "Search a destination on the map first.", "warning");
    return;
  }
  fetch("/save-place/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({
      name: lastSearchedPlace,
      lat: lastSearchedLat,
      lon: lastSearchedLon,
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "ok") {
        showToast("Saved!", `${lastSearchedPlace} added to your saved places.`, "success");
      }
    })
    .catch(() => {
      showToast("Error", "Could not save place. Try again.", "error");
    });
}

function saveFromPopup(name, lat, lon) {
  fetch("/save-place/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({ name, lat, lon }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "ok") {
        showToast("Saved!", `${name} added to your saved places.`, "success");
      }
    })
    .catch(() => {
      showToast("Error", "Could not save place. Try again.", "error");
    });
}

function fetchHotels() {
  if (!lastSearchedLat || !lastSearchedLon) {
    addChatBotMessage("<p style='color: #ef4444;'>Search a destination first.</p>");
    return;
  }

  fetch("/get-places/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken")
    },
    body: JSON.stringify({ lat: lastSearchedLat, lon: lastSearchedLon, place: lastSearchedPlace })
  })
    .then(res => res.json())
    .then(hotels => {
      if (!hotels.length) {
        addChatBotMessage("<p>No hotels found near <strong>" + lastSearchedPlace + "</strong>.</p>");
        return;
      }
      let html = "<strong>🏨 Hotels near " + lastSearchedPlace + ":</strong><br><div style='margin-top:10px;display:flex;flex-direction:column;gap:10px;'>";
      for (const h of hotels) {
        html += "<div style='background:rgba(60,30,15,0.6);border-radius:8px;padding:10px;display:flex;gap:12px;align-items:center;'>";
        if (h.thumbnail) html += "<img src='" + h.thumbnail + "' style='width:70px;height:55px;object-fit:cover;border-radius:6px;'>";
        html += "<div><strong>" + h.title + "</strong>";
        if (h.address) html += "<br><span style='font-size:0.85rem;opacity:0.8;'>" + h.address + "</span>";
        if (h.rating) html += "<br><span>⭐ " + h.rating + " (" + h.reviews + " reviews)</span>";
        if (h.price) html += "<br><span style='color:#059669;font-weight:700;'>" + h.price + "</span>";
        html += "</div></div>";
      }
      html += "</div>";
      addChatBotMessage(html);
    })
    .catch(() => {
      addChatBotMessage("<p style='color: #ef4444;'>Failed to fetch hotels. Try again.</p>");
    });
}


function useCurrentLocation() {
  if (userMarker) {
    const latlng = userMarker.getLatLng();
    if (startMarker) startMarker.remove();

    startMarker = L.marker(latlng).addTo(map).bindPopup("Current location locked").openPopup();
    document.getElementById('startLocation').value = `${latlng.lat.toFixed(5)},${latlng.lng.toFixed(5)}`;
    if (endMarker) showRoute();
  } else if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(position => {
      const lat = position.coords.latitude;
      const lon = position.coords.longitude;

      if (startMarker) startMarker.remove();
      startMarker = L.marker([lat, lon]).addTo(map).bindPopup("Current location locked").openPopup();
      document.getElementById('startLocation').value = `${lat.toFixed(5)},${lon.toFixed(5)}`;
      if (endMarker) showRoute();
    }, () => {
      alert("Unable to securely access localized positioning data.");
    });
  } else {
    alert("Geolocation mechanics are restricted on this host framework browser layout.");
  }
}

function showRoute() {
  if (!startMarker || !endMarker) {
    return;
  }

  if (routeControl) {
    map.removeControl(routeControl);
  }

  routeControl = L.Routing.control({
    waypoints: [
      startMarker.getLatLng(),
      endMarker.getLatLng()
    ],
    routeWhileDragging: true,
    show: false,
    collapsible: true,
    addWaypoints: false,
    createMarker: () => null
  }).addTo(map);

  routeControl.on('routesfound', function (e) {
    const route = e.routes[0];
    const summary = route.summary;

    document.getElementById("routeSummary").innerHTML = `
      <div class="route-stat"><i class="fa-solid fa-road"></i> ${(summary.totalDistance / 1000).toFixed(2)} km</div>
      <div class="route-stat"><i class="fa-solid fa-clock"></i> ${(summary.totalTime / 60).toFixed(1)} min</div>
    `;

    let html = '<ol class="directions-list">';
    for (const step of route.instructions) {
      const dist = step.distance >= 1000
        ? (step.distance / 1000).toFixed(2) + " km"
        : Math.round(step.distance) + " m";
      html += `<li><span>${step.text}</span> <em>${dist}</em></li>`;
    }
    html += "</ol>";
    document.getElementById("routeInstructions").innerHTML = html;
    document.getElementById("routeInfoPanel").style.display = "block";
  });
}

function closeRoutePanel() {
  document.getElementById("routeInfoPanel").style.display = "none";
}


function addChatBotMessage(html) {
  const chatMessages = document.getElementById("chatMessages");
  if (!chatMessages) return;
  const botDiv = document.createElement("div");
  botDiv.className = "message bot-bubble";
  botDiv.innerHTML = html;
  chatMessages.appendChild(botDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}



function handleStartLocation() {
  const input = document.getElementById('startLocation').value.trim();
  const coordPattern = /^-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?$/;

  if (input === "") {
    useCurrentLocation();
  } else if (coordPattern.test(input)) {
    const [lat, lon] = input.split(',').map(Number);

    if (startMarker) startMarker.remove();

    startMarker = L.marker([lat, lon]).addTo(map).bindPopup("Origin Coordinates Set").openPopup();
    map.setView([lat, lon], 13);
    showRoute();
  } else {
    setStartLocationFromInput();
  }
}

function setStartLocationFromInput() {
  const place = document.getElementById('startLocation').value.trim();

  fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(place)}`)
    .then(res => res.json())
    .then(data => {
      if (data.length > 0) {
        const lat = parseFloat(data[0].lat);
        const lon = parseFloat(data[0].lon);

        map.setView([lat, lon], 13);

        if (startMarker) {
          startMarker.setLatLng([lat, lon]);
        } else {
          startMarker = L.marker([lat, lon]).addTo(map);
        }

        startMarker.bindPopup(`<strong>Origin:</strong> ${place}`).openPopup();
        showRoute();
      }
    });
}





let driveModeEnabled = false;
let currentLocationMarker = null;

function toggleDriveMode() {
  driveModeEnabled = !driveModeEnabled;
  document.getElementById('driveModeBtn').innerHTML = driveModeEnabled ?
    `<i class="fa-solid fa-car-slash"></i> Disable Drive Mode` :
    `<i class="fa-solid fa-car"></i> Enable Drive Mode`;

  if (driveModeEnabled) {
    map.locate({ watch: true, enableHighAccuracy: true });
  } else {
    map.stopLocate();
    if (currentLocationMarker) {
      map.removeLayer(currentLocationMarker);
      currentLocationMarker = null;
    }
  }
}

map.on('locationfound', (e) => {
  if (driveModeEnabled) {
    if (!currentLocationMarker) {
      currentLocationMarker = L.marker(e.latlng).addTo(map).bindPopup("Driving Mode Tracking Active");
    } else {
      currentLocationMarker.setLatLng(e.latlng);
    }
    map.setView(e.latlng, 16);
  }
});

map.on('locationerror', () => {
  if (driveModeEnabled) {
    alert("⚠️ Location telemetry failed or was interrupted.");
    driveModeEnabled = false;
    document.getElementById('driveModeBtn').innerHTML = `<i class="fa-solid fa-car"></i> Enable Drive Mode`;
  }
});

function toggleChat() {
  const dashboard = document.querySelector(".workspace-dashboard");
  dashboard.classList.toggle("chat-collapsed");
  setTimeout(() => map.invalidateSize(), 350);
}

/* ==========================================
   CHIP PROMPT HELPERS (inlined from chatbot.js)
   ========================================== */
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
      const input = document.querySelector('[name="message"]');
      if (input) {
        input.value = `Create a detailed day-by-day travel itinerary for ${data.place}. Include attractions, restaurants, and tips.`;
        input.closest('form').dispatchEvent(new Event('submit', { cancelable: true }));
      }
    })
    .catch(() => {
      showToast("Error", "Could not fetch place data. Try again.", "error");
    });
}

function sendChipPrompt(prompt) {
  if (!prompt) return;
  const input = document.querySelector('[name="message"]');
  if (input) {
    input.value = prompt;
    input.closest('form').dispatchEvent(new Event('submit', { cancelable: true }));
  }
}
