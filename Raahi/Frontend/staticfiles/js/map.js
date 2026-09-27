// Leaflet map setup for Raahi

// Destination coords sent by the Django view ("" or null when there is none)
const destinationData = document.getElementById('destination-data');
let destination = destinationData
	? JSON.parse(destinationData.textContent)
	: null;

// Start coords (for routing) sent by the Django view
const startData = document.getElementById('start-data');
let start = startData ? JSON.parse(startData.textContent) : null;

// Start at the searched place, then the start point; fall back to Delhi with no search yet
const startPosition = destination
	? [destination.lat, destination.lon]
	: start
		? [start.lat, start.lon]
		: [28.6139, 77.209];
const startZoom = destination || start ? 14 : 13;

var map = L.map('map').setView(startPosition, startZoom);

// --- motion helpers -------------------------------------------------------
// animate.css (class-based), anime.js (sequenced) and FormKit Auto-Animate
// (list reflow) each cover a different case; none of them may override a
// preference for reduced motion.
const REDUCED_MOTION = window.matchMedia(
	'(prefers-reduced-motion: reduce)',
).matches;

// Re-add an animate.css class so the effect replays on repeated triggers.
function playClass(el, className) {
	if (!el || REDUCED_MOTION) {
		return;
	}
	el.classList.remove('animate__animated', className);
	void el.offsetWidth; // force reflow so the animation restarts
	el.classList.add('animate__animated', className);
}

// Anime.js wrapper that respects reduced-motion and CDN failures.
function animeSafe(params) {
	if (typeof window.anime !== 'function' || REDUCED_MOTION) {
		if (params.complete) params.complete();
		return;
	}
	window.anime(params);
}
// --------------------------------------------------------------------------

// Base layers: OpenStreetMap streets (default) and Esri World Imagery satellite
const streetLayer = L.tileLayer(
	'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
	{
		maxZoom: 19,
		referrerPolicy: 'origin',
		attribution:
			'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
	},
);

const satelliteLayer = L.tileLayer(
	'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
	{
		maxZoom: 19,
		referrerPolicy: 'origin',
		attribution:
			'Tiles &copy; Esri &mdash; Source: Esri, Vantor, Earthstar Geographics, and the GIS User Community',
	},
);

streetLayer.addTo(map);

// Basemap switcher (top-left, under the zoom buttons). Markers, popups and routes
// live in their own panes above the tiles, so they work on both basemaps.
const baseLayers = {
	Street: streetLayer,
	Satellite: satelliteLayer,
};
L.control
	.layers(baseLayers, null, { position: 'topleft' })
	.addTo(map);

// Track active basemap for animation
let activeBase = 'Street';
map.on('baselayerchange', function (e) {
	const newBase = e.name;
	if (newBase !== activeBase && !REDUCED_MOTION) {
		const container = document.getElementById('map');
		if (container && typeof window.anime === 'function') {
			window.anime({
				targets: container,
				opacity: [1, 0.6, 1],
				duration: 350,
				easing: 'easeInOutQuad',
			});
		}
		activeBase = newBase;
	}
});

// --- Grand entrance sequence for the map page (anime.js) ---
// Runs once on load: map fade+scale, then searchbar slide up, then FAB pop-in.
function runMapEntrance() {
	if (typeof window.anime !== 'function' || REDUCED_MOTION) {
		// Instant show for reduced motion
		const els = document.querySelectorAll('.searchbar, .chat-fab');
		els.forEach((el) => (el.style.opacity = ''));
		return;
	}

	// Elements start hidden via inline style (set below)
	const mapEl = document.getElementById('map');
	const searchbar = document.querySelector('.searchbar');
	const fab = document.querySelector('.chat-fab');

	// Prepare initial state
	[searchbar, fab].forEach((el) => {
		if (el) el.style.opacity = '0';
	});
	if (mapEl) mapEl.style.opacity = '0';

	window.anime
		.timeline({ easing: 'easeOutCubic' })
		.add({
			targets: mapEl,
			opacity: [0, 1],
			scale: [0.98, 1],
			duration: 600,
		})
		.add({
			targets: searchbar,
			opacity: [0, 1],
			translateY: [20, 0],
			duration: 450,
		}, '-=300')
		.add({
			targets: fab,
			opacity: [0, 1],
			scale: [0.7, 1],
			duration: 400,
			easing: 'easeOutElastic(1, .6)',
		}, '-=200');

	// Safety net
	setTimeout(() => {
		[mapEl, searchbar, fab].forEach((el) => {
			if (el) {
				el.style.opacity = '';
				el.style.transform = '';
			}
		});
	}, 3000);
}

// Initially hide entrance elements (anime will reveal them)
const entranceEls = document.querySelectorAll('.searchbar, .chat-fab');
entranceEls.forEach((el) => (el.style.opacity = '0'));

// Run entrance after a tick so CSS is applied
requestAnimationFrame(() => {
	requestAnimationFrame(runMapEntrance);
});

// Route and marker from the current search. Handles let us remove the old
// result before drawing a new one, so repeat htmx searches never stack.
let routeControl = null;
let resultMarker = null;

function clearResults() {
	if (routeControl) {
		map.removeControl(routeControl);
		routeControl = null;
	}
	if (resultMarker) {
		map.removeLayer(resultMarker);
		resultMarker = null;
	}
}

function showSearchErrors(errors) {
	const box = document.getElementById('search-messages');
	box.innerHTML = '';
	(errors || []).forEach(function (msg) {
		const p = document.createElement('p');
		p.className = 'form-message error';
		p.textContent = msg;
		box.appendChild(p);
	});

	// animate.css: a failed search should read as a refusal, not as silence
	if ((errors || []).length) {
		playClass(box, 'animate__shakeX');
	}
}

// Vanilla JS Leaflet rendering only. htmx just delivers the data,
// this function draws it. Called once for first paint, then after
// every htmx search response. Totals and turn-by-turn steps are shown by
// Leaflet Routing Machine's own panel, so nothing is duplicated here.
function updateMap(newStart, newDestination) {
	const hadRoute = !!routeControl;
	const hadMarker = !!resultMarker;
	const isNewRoute = newStart && newDestination;

	start = newStart;
	destination = newDestination;
	clearResults();

	// Animate map camera transition for smoother feel
	const targetLatLng = newDestination
		? [newDestination.lat, newDestination.lon]
		: newStart
			? [newStart.lat, newStart.lon]
			: null;
	if (targetLatLng && !REDUCED_MOTION) {
		map.flyTo(targetLatLng, isNewRoute ? 13 : 14, {
			duration: hadRoute || hadMarker ? 1.2 : 0.8,
			easeLinearity: 0.25,
		});
	} else if (targetLatLng) {
		map.setView(targetLatLng, isNewRoute ? 13 : 14);
	}

	if (isNewRoute) {
		// Show calculating state with anime.js pulsing searchbar (uses theme primary #E85D04)
		const searchbar = document.querySelector('.searchbar');
		if (searchbar && typeof window.anime === 'function' && !REDUCED_MOTION) {
			window.anime({
				targets: searchbar,
				boxShadow: [
					'0 0 0 0 rgba(232, 93, 4, 0)',
					'0 0 0 8px rgba(232, 93, 4, 0.15)',
					'0 0 0 0 rgba(232, 93, 4, 0)',
				],
				duration: 1500,
				loop: true,
				easing: 'easeInOutSine',
			});
			searchbar.dataset.calculating = '1';
		}

		routeControl = L.Routing.control({
			waypoints: [
				L.latLng(start.lat, start.lon),
				L.latLng(destination.lat, destination.lon),
			],
			addWaypoints: false,
			routeWhileDragging: false,
			collapsible: true,
			show: true,
			lineOptions: {
				styles: [{ color: '#E85D04', weight: 5, opacity: 0.85 }],
				extendToWaypoints: true,
				missingRouteTolerance: 0,
			},
		}).addTo(map);

		routeControl.on('routesfound', function () {
			// Stop calculating animation
			const searchbar = document.querySelector('.searchbar');
			if (searchbar && searchbar.dataset.calculating) {
				if (typeof window.anime === 'function') {
					window.anime.remove(searchbar);
				}
				searchbar.style.boxShadow = '';
				delete searchbar.dataset.calculating;
			}

			const panel = document.querySelector('.leaflet-routing-container');
			// animate.css: the route panel arrives from the side
			playClass(panel, 'animate__slideInRight');

			// FormKit Auto-Animate: a recalculated route reflows its steps
			if (panel && typeof window.autoAnimate === 'function') {
				if (panel.dataset.autoAnimated !== '1') {
					panel.dataset.autoAnimated = '1';
					window.autoAnimate(panel, { duration: 250 });
				}
			}

			// Animate waypoint markers popping in
			animeSafe({
				targets: '.leaflet-routing-waypoint-icon',
				scale: [0, 1],
				opacity: [0, 1],
				duration: 400,
				delay: window.anime ? window.anime.stagger(120) : 0,
				easing: 'easeOutElastic(1, .7)',
			});

			// Animate route line drawing (anime.js on stroke-dashoffset)
			animeSafe({
				targets: '.leaflet-routing-line path',
				strokeDashoffset: [window.anime ? window.anime.setDashoffset : 0, 0],
				duration: 1200,
				easing: 'easeOutCubic',
			});
		});
		routeControl.on('routingerror', function () {
			const searchbar = document.querySelector('.searchbar');
			if (searchbar && searchbar.dataset.calculating) {
				if (typeof window.anime === 'function') {
					window.anime.remove(searchbar);
				}
				searchbar.style.boxShadow = '';
				delete searchbar.dataset.calculating;
			}
			showSearchErrors(['Could not calculate the route. Please try again.']);
		});
	} else if (newDestination) {
		// Destination-only: marker with bounce-in
		const latlng = [newDestination.lat, newDestination.lon];
		resultMarker = L.marker(latlng)
			.addTo(map)
			.bindPopup(newDestination.name || 'Your destination');

		// Pop-in animation via anime.js on the marker icon
		setTimeout(() => {
			const icon = map._panes.markerPane.querySelector('.leaflet-marker-icon:last-child');
			animeSafe({
				targets: icon,
				scale: [0, 1.15, 1],
				opacity: [0, 1],
				duration: 500,
				easing: 'easeOutElastic(1, .6)',
			});
		}, 50);

		resultMarker.openPopup();
		// Popup entrance animation
		setTimeout(() => {
			const popup = document.querySelector('.leaflet-popup');
			playClass(popup, 'animate__zoomIn');
		}, 100);
	} else if (newStart) {
		const latlng = [newStart.lat, newStart.lon];
		resultMarker = L.marker(latlng)
			.addTo(map)
			.bindPopup(newStart.name || 'Your starting point');

		setTimeout(() => {
			const icon = map._panes.markerPane.querySelector('.leaflet-marker-icon:last-child');
			animeSafe({
				targets: icon,
				scale: [0, 1.15, 1],
				opacity: [0, 1],
				duration: 500,
				easing: 'easeOutElastic(1, .6)',
			});
		}, 50);

		resultMarker.openPopup();
		setTimeout(() => {
			const popup = document.querySelector('.leaflet-popup');
			playClass(popup, 'animate__zoomIn');
		}, 100);
	}
}

// First paint (from json_script tags, both empty on fresh load)
updateMap(start, destination);

// Initialize Auto-Animate on dynamic lists and message containers
if (typeof window.autoAnimate === 'function') {
	const searchMessages = document.getElementById('search-messages');
	if (searchMessages) {
		window.autoAnimate(searchMessages, { duration: 200 });
	}
}

// "Use my location" button: fills the start point with the device's coordinates
const locationButton = document.getElementById('use-location');
const startInput = document.getElementById('id_start_location');
const startLatInput = document.getElementById('id_start_lat');
const startLonInput = document.getElementById('id_start_lon');
const locationMessage = document.getElementById('location-message');
const locationButtonLabel = locationButton ? locationButton.textContent : '';
const reverseUrl = locationButton ? locationButton.dataset.reverseUrl : '';

const GEOLOCATION_OPTIONS = { enableHighAccuracy: true, timeout: 10000 };

const GEOLOCATION_ERRORS = {
	1: 'Location access was denied. Allow location access in your browser or type a starting point.',
	2: 'Your current location is unavailable. Please try again or type a starting point.',
	3: 'Getting your location timed out. Please try again or type a starting point.',
};

let userMarker = null;
let startTouched = false;

function showLocationMessage(text, type) {
	locationMessage.textContent = text || '';
	locationMessage.className = type ? 'form-message ' + type : 'form-message';
	locationMessage.hidden = !text;
	if (text) {
		playClass(locationMessage, 'animate__fadeInUp');
	}
}

function showUserOnMap(latitude, longitude) {
	const latlng = [latitude, longitude];

	if (userMarker) {
		// Smooth move with anime.js
		if (!REDUCED_MOTION && typeof window.anime === 'function') {
			const icon = userMarker.getElement();
			if (icon) {
				window.anime({
					targets: icon,
					translateY: [-5, 0],
					duration: 400,
					easing: 'easeOutQuad',
				});
			}
		}
		userMarker.setLatLng(latlng);
	} else {
		userMarker = L.marker(latlng).addTo(map).bindPopup('Your location');
		// Pop-in animation for new marker
		setTimeout(() => {
			const icon = map._panes.markerPane.querySelector('.leaflet-marker-icon:last-child');
			animeSafe({
				targets: icon,
				scale: [0, 1.2, 1],
				opacity: [0, 1],
				duration: 600,
				easing: 'easeOutElastic(1, .6)',
			});
		}, 50);
	}

	// Smooth camera fly-to
	if (!REDUCED_MOTION) {
		map.flyTo(latlng, 14, { duration: 1.5, easeLinearity: 0.25 });
	} else {
		map.setView(latlng, 14);
	}
}

async function applyCurrentPosition(latitude, longitude) {
	// exact coordinates go into the hidden fields, the Django view uses them directly
	startLatInput.value = latitude;
	startLonInput.value = longitude;

	showUserOnMap(latitude, longitude);

	// ask the backend for a readable name for these coordinates
	let name = 'Current location';
	try {
		const response = await fetch(
			reverseUrl + '?lat=' + latitude + '&lon=' + longitude,
		);
		if (response.ok) {
			const data = await response.json();
			name = data.name || name;
		}
	} catch (error) {
		console.error(
			'Could not fetch a name for the current location:',
			error,
		);
	}

	startInput.value = name;

	return name;
}

async function useCurrentLocation() {
	if (!navigator.geolocation) {
		showLocationMessage(
			'Geolocation is not supported by this browser.',
			'error',
		);
		return;
	}

	locationButton.disabled = true;
	locationButton.textContent = 'Locating...';
	showLocationMessage('Getting your location...');

	// Pulsing animation on button while locating (uses theme primary #E85D04)
	if (typeof window.anime === 'function' && !REDUCED_MOTION) {
		window.anime({
			targets: locationButton,
			scale: [1, 1.02, 1],
			boxShadow: [
				'0 0 0 0 rgba(232, 93, 4, 0.4)',
				'0 0 0 10px rgba(232, 93, 4, 0)',
				'0 0 0 0 rgba(232, 93, 4, 0.4)',
			],
			duration: 1500,
			loop: true,
			easing: 'easeInOutSine',
		});
		locationButton.dataset.locating = '1';
	}

	navigator.geolocation.getCurrentPosition(
		async function (position) {
			// Stop pulsing
			if (locationButton.dataset.locating) {
				if (typeof window.anime === 'function') {
					window.anime.remove(locationButton);
				}
				locationButton.style.transform = '';
				locationButton.style.boxShadow = '';
				delete locationButton.dataset.locating;
			}

			const name = await applyCurrentPosition(
				position.coords.latitude,
				position.coords.longitude,
			);
			showLocationMessage(
				'Using ' + name + ' as the starting point.',
				'success',
			);
			locationButton.disabled = false;
			locationButton.textContent = locationButtonLabel;

			// Success flash on button (theme primary -> success -> white)
			animeSafe({
				targets: locationButton,
				backgroundColor: ['#E85D04', '#2A9D8F', '#FFFFFF'],
				duration: 600,
				easing: 'easeOutQuad',
				complete: () => (locationButton.style.backgroundColor = ''),
			});
		},
		function (error) {
			if (locationButton.dataset.locating) {
				if (typeof window.anime === 'function') {
					window.anime.remove(locationButton);
				}
				locationButton.style.transform = '';
				locationButton.style.boxShadow = '';
				delete locationButton.dataset.locating;
			}

			showLocationMessage(
				GEOLOCATION_ERRORS[error.code] ||
					'Could not get your location. Please try again.',
				'error',
			);
			locationButton.disabled = false;
			locationButton.textContent = locationButtonLabel;

			// Error shake on button
			playClass(locationButton, 'animate__shakeX');
		},
		GEOLOCATION_OPTIONS,
	);
}

// On page load: centre the map on the user's location and prefill the start point.
// Skipped (keeping the Delhi default) when a search is already on screen.
function locateOnLoad() {
	if (destination || start) {
		return;
	}

	if (!navigator.geolocation) {
		return;
	}

	navigator.geolocation.getCurrentPosition(
		async function (position) {
			if (startTouched) {
				// the user already typed another start point, leave the form alone
				showLocationMessage('');
				return;
			}

			const name = await applyCurrentPosition(
				position.coords.latitude,
				position.coords.longitude,
			);
			showLocationMessage(
				'Using ' + name + ' as the starting point.',
				'success',
			);
		},
		function (error) {
			if (error.code === 1) {
				showLocationMessage(
					'Location access is off, showing Delhi by default. Type a starting point or allow location access in your browser.',
				);
			} else {
				showLocationMessage(
					'Could not detect your location, showing Delhi by default. Type a starting point to change it.',
				);
			}
		},
		GEOLOCATION_OPTIONS,
	);
}

if (locationButton) {
	locationButton.addEventListener('click', useCurrentLocation);

	// editing the start point by hand means the text (not the stored coordinates) is used
	startInput.addEventListener('input', function () {
		startTouched = true;
		startLatInput.value = '';
		startLonInput.value = '';

		// Subtle feedback on input
		playClass(startInput, 'animate__pulse');
	});
}

locateOnLoad();

// htmx transport -> vanilla JS render. Fires after every search-form POST.
document.body.addEventListener('htmx:afterRequest', function (event) {
	// ignore anything that isn't our search form
	if (
		!event.detail.elt ||
		!event.detail.elt.classList.contains('search-form')
	) {
		return;
	}
	let data;
	try {
		data = JSON.parse(event.detail.xhr.response);
	} catch (e) {
		return;
	}
	if (!data || !('start' in data && 'destination' in data)) {
		return;
	}

	// Animate form submit feedback
	const form = event.detail.elt;
	playClass(form, 'animate__pulse');

	showSearchErrors(data.errors || []);
	updateMap(data.start, data.destination);
});

// Travel search: fetch nearby places and display them as map markers.
// Tabs switch the amenity category; results are clickable to zoom.
(function () {
	'use strict';

	const travelSearch = document.getElementById('travel-search');
	if (!travelSearch || typeof L === 'undefined') {
		return; // not on the map page, or Leaflet failed to load
	}

	const travelTabs = travelSearch.querySelectorAll('.travel-tab');
	const travelResults = document.getElementById('travel-results');
	let travelLayer = null;

	// Inline SVGs keyed by the `icon` name the travel API returns.
	// Same stroke style as the rest of the site (see templates/icons/).
	const ICONS = {
		pin: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
		restaurant: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/><path d="M7 2v20"/><path d="M21 15V2a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3zm0 0v7"/></svg>',
		hotel: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01M16 6h.01M12 6h.01M8 10h.01M16 10h.01M12 10h.01M8 14h.01M16 14h.01M12 14h.01"/></svg>',
		cafe: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/><path d="M6 1v3M10 1v3M14 1v3"/></svg>',
		bar: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3h14l-7 8-7-8z"/><path d="M12 11v9"/><path d="M8 21h8"/></svg>',
		attraction: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 22h18"/><path d="M6 18v-7M10 18v-7M14 18v-7M18 18v-7"/><path d="M12 2 3 7h18l-9-5z"/></svg>',
		park: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2 5 12h14l-7-10z"/><path d="M5 12v8M19 12v8M9 20h6"/></svg>',
		pharmacy: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v8M8 12h8"/></svg>',
		fuel: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 22h12"/><path d="M4 9h10"/><path d="M14 22V4a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v18"/><path d="M20 9h-2a2 2 0 0 0-2 2v6h4"/><path d="M18 17h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/></svg>',
	};

	function travelIcon(key) {
		return ICONS[key] || ICONS.pin;
	}

	function clearTravelLayer() {
		if (travelLayer) {
			map.removeLayer(travelLayer);
			travelLayer = null;
		}
	}

	function escapeHtml(text) {
		const div = document.createElement('div');
		div.textContent = text || '';
		return div.innerHTML;
	}

	async function loadCategory(category) {
		const center = map.getCenter();
		travelResults.innerHTML = '<p class="form-message">Searching nearby...</p>';
		let data;
		try {
			const response = await fetch(
				'/travel/nearby/?lat=' + center.lat.toFixed(6) +
				'&lon=' + center.lng.toFixed(6) +
				'&category=' + encodeURIComponent(category),
			);
			data = await response.json();
		} catch (error) {
			travelResults.innerHTML = '<p class="form-message error">Could not load nearby places.</p>';
			return;
		}
		if (!response_ok(data)) {
			travelResults.innerHTML = '<p class="form-message error">Could not load nearby places.</p>';
			return;
		}

		clearTravelLayer();
		const markers = [];
		(data.places || []).forEach(function (place) {
			if (place.lat == null || place.lon == null) {
				return;
			}
			const marker = L.marker([place.lat, place.lon]).bindPopup(
				'<div class="map-popup">' + travelIcon(place.icon) +
				'<div><strong>' + escapeHtml(place.name) + '</strong>' +
				(place.address ? '<br>' + escapeHtml(place.address) : '') + '</div></div>',
			);
			markers.push(marker);
		});
		if (markers.length) {
			travelLayer = L.featureGroup(markers).addTo(map);
		}

		if (!(data.places || []).length) {
			travelResults.innerHTML = '<p class="form-message">Nothing found nearby. Try another area or category.</p>';
			return;
		}
		travelResults.innerHTML = '';
		(data.places || []).slice(0, 30).forEach(function (place, index) {
			const item = document.createElement('div');
			item.className = 'travel-item';
			item.innerHTML = travelIcon(place.icon) + '<span>' + escapeHtml(place.name || 'Unknown') + '</span>';
			item.addEventListener('click', function () {
				if (place.lat != null && place.lon != null) {
					map.setView([place.lat, place.lon], 16);
					if (markers[index]) {
						markers[index].openPopup();
					}
				}
			});
			travelResults.appendChild(item);
		});
	}

	function response_ok(data) {
		return data && Array.isArray(data.places);
	}

	travelTabs.forEach(function (tab) {
		tab.addEventListener('click', function () {
			travelTabs.forEach(function (t) {
				t.classList.remove('active');
			});
			tab.classList.add('active');
			loadCategory(tab.dataset.category);
		});
	});
})();
