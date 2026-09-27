// Raahi assistant chat (vanilla JS + htmx-style polling).
// Slow work (Ollama, web research) runs in Celery: the view returns a
// task_id instantly, and this script polls /tasks/<id>/ until SUCCESS.
//
// Reads the current destination name from the page (chat.js loads after
// map.js, so the `destination` variable set there is in scope).

(function () {
	'use strict';

	const chatForm = document.getElementById('chat-form');
	if (!chatForm) {
		return; // not on the map page
	}

	const chatInput = document.getElementById('chat-input');
	const chatMessages = document.getElementById('chat-messages');
	const chatUrl = chatForm.dataset.chatUrl;
	const itineraryUrl = chatForm.dataset.itineraryUrl;
	const chatModal = document.querySelector('.chat-modal');
	const chatModalBox = document.querySelector('.chat-modal-box');
	const chatFab = document.querySelector('.chat-fab');

	const REDUCED_MOTION = window.matchMedia(
		'(prefers-reduced-motion: reduce)',
	).matches;

	// Anime.js wrapper
	function animeSafe(params) {
		if (typeof window.anime !== 'function' || REDUCED_MOTION) {
			if (params.complete) params.complete();
			return;
		}
		window.anime(params);
	}

	// Animate.css helper
	function playClass(el, className) {
		if (!el || REDUCED_MOTION) return;
		el.classList.remove('animate__animated', className);
		void el.offsetWidth;
		el.classList.add('animate__animated', className);
	}

	// --- Modal open/close orchestration (anime.js) ---
	window.raahiChatOpen = function (isOpening) {
		if (typeof window.anime !== 'function' || REDUCED_MOTION) return;

		if (isOpening) {
			// FAB morphs into modal
			window.anime({
				targets: chatFab,
				scale: [1, 0.8, 0],
				opacity: [1, 1, 0],
				duration: 300,
				easing: 'easeInCubic',
				complete: () => (chatFab.style.display = 'none'),
			});

			// Modal entrance
			chatModalBox.style.transform = 'translateY(40px) scale(0.95)';
			chatModalBox.style.opacity = '0';
			window.anime({
				targets: chatModalBox,
				translateY: [40, 0],
				scale: [0.95, 1],
				opacity: [0, 1],
				duration: 450,
				easing: 'easeOutCubic',
			});

			// Backdrop fade-in
			const backdrop = document.querySelector('.chat-modal-backdrop');
			backdrop.style.opacity = '0';
			window.anime({
				targets: backdrop,
				opacity: [0, 1],
				duration: 300,
			});

			// Suggestion chips stagger in
			window.anime({
				targets: '#chatbot .chat-suggestions .suggestion-btn',
				opacity: [0, 1],
				translateY: [16, 0],
				duration: 450,
				delay: window.anime.stagger(60),
				easing: 'easeOutCubic',
			});
		} else {
			// Modal exit
			window.anime({
				targets: chatModalBox,
				translateY: [0, 30],
				scale: [1, 0.95],
				opacity: [1, 0],
				duration: 250,
				easing: 'easeInCubic',
			});

			const backdrop = document.querySelector('.chat-modal-backdrop');
			window.anime({
				targets: backdrop,
				opacity: [1, 0],
				duration: 200,
			});

			// FAB pop back
			setTimeout(() => {
				chatFab.style.display = '';
				window.anime({
					targets: chatFab,
					scale: [0, 1.1, 1],
					opacity: [0, 1],
					duration: 400,
					easing: 'easeOutElastic(1, .6)',
				});
			}, 150);
		}
	};

	// Alpine calls this through x-effect each time the assistant opens
	const originalOpen = window.raahiChatOpen;
	window.raahiChatOpen = function (isOpening) {
		if (isOpening === undefined) {
			// Called from Alpine x-effect (open is truthy)
			return originalOpen(true);
		}
		return originalOpen(isOpening);
	};

	// Enable FormKit Auto-Animate for chat messages stream
	if (chatMessages && typeof window.autoAnimate === 'function') {
		window.autoAnimate(chatMessages, { duration: 250 });
	}

	function csrfToken() {
		const match = document.cookie.match(/csrftoken=([^;]+)/);
		return match ? decodeURIComponent(match[1]) : '';
	}

	function currentPlaceName() {
		if (
			typeof destination !== 'undefined' &&
			destination &&
			destination.name
		) {
			return destination.name;
		}
		return '';
	}

	function addMessage(text, who, options = {}) {
		const div = document.createElement('div');
		div.className = 'chat-message ' + who;
		const span = document.createElement('span');
		span.textContent = text;
		div.appendChild(span);
		chatMessages.appendChild(div);

		// Entrance animation for new messages (anime.js)
		if (!REDUCED_MOTION && typeof window.anime === 'function') {
			div.style.opacity = '0';
			div.style.transform = 'translateY(12px)';
			window.anime({
				targets: div,
				opacity: [0, 1],
				translateY: [12, 0],
				duration: 350,
				easing: 'easeOutCubic',
				delay: options.delay || 0,
				complete: () => {
					div.style.opacity = '';
					div.style.transform = '';
				},
			});
		}

		chatMessages.scrollTop = chatMessages.scrollHeight;
		return div;
	}

	function pollTask(taskId, typingEl, onDone) {
		const timer = setInterval(async function () {
			let response;
			try {
				response = await fetch('/tasks/' + taskId + '/');
			} catch (error) {
				clearInterval(timer);
				typingEl.remove();
				addMessage(
					'Could not reach the server. Is it still running?',
					'assistant',
				);
				return;
			}
			let data;
			try {
				data = await response.json();
			} catch (error) {
				clearInterval(timer);
				typingEl.remove();
				addMessage(
					'Got an unreadable reply from the server.',
					'assistant',
				);
				return;
			}
			if (data.status === 'SUCCESS') {
				clearInterval(timer);
				// Typing indicator fade out
				animeSafe({
					targets: typingEl,
					opacity: [1, 0],
					translateY: [0, -8],
					duration: 200,
					easing: 'easeInQuad',
					complete: () => typingEl.remove(),
				});
				onDone(data.result || {});
			} else if (data.status === 'FAILURE') {
				clearInterval(timer);
				animeSafe({
					targets: typingEl,
					opacity: [1, 0],
					translateY: [0, -8],
					duration: 200,
					easing: 'easeInQuad',
					complete: () => typingEl.remove(),
				});
				addMessage(
					data.error || 'Something went wrong on the server.',
					'assistant',
				);
			}
			// else PENDING/STARTED/RETRY: keep polling
		}, 3000);
	}

	async function postForm(url, fields) {
		const body = new URLSearchParams(fields);
		const response = await fetch(url, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/x-www-form-urlencoded',
				'X-CSRFToken': csrfToken(),
			},
			body: body.toString(),
		});
		let data = null;
		try {
			data = await response.json();
		} catch (error) {
			data = null;
		}
		if (!response.ok) {
			throw new Error(
				(data && (data.error || data.errors)) || 'Request failed.',
			);
		}
		return data;
	}

	async function askQuestion(question, place) {
		addMessage(question, 'user');
		chatInput.value = '';

		// Input clear animation
		playClass(chatInput, 'animate__flash');

		const typingEl = addMessage('Raahi is thinking...', 'assistant typing', { delay: 100 });
		typingEl.classList.add('typing-indicator');

		// Pulsing dots animation on typing indicator
		if (typeof window.anime === 'function' && !REDUCED_MOTION) {
			const dots = typingEl.querySelector('span');
			if (dots) {
				let dotCount = 0;
				const interval = setInterval(() => {
					if (!document.body.contains(typingEl)) {
						clearInterval(interval);
						return;
					}
					dotCount = (dotCount + 1) % 4;
					dots.textContent = 'Raahi is thinking' + '.'.repeat(dotCount);
				}, 500);
				typingEl.dataset.dotInterval = interval;
			}
		}

		let data;
		try {
			data = await postForm(chatUrl, {
				question: question,
				place: place,
			});
		} catch (error) {
			if (typingEl.dataset.dotInterval) clearInterval(typingEl.dataset.dotInterval);
			typingEl.remove();
			addMessage(error.message, 'assistant');
			return;
		}
		pollTask(taskIdFix(data), typingEl, function (result) {
			if (typingEl.dataset.dotInterval) clearInterval(typingEl.dataset.dotInterval);
			if (result.error) {
				addMessage(result.error, 'assistant', { delay: 50 });
				// Error shake on the message
				setTimeout(() => {
					const lastMsg = chatMessages.lastElementChild;
					playClass(lastMsg, 'animate__shakeX');
				}, 100);
			} else {
				addMessage(result.reply || 'No reply came back.', 'assistant', { delay: 50 });
			}
		});
	}

	function taskIdFix(data) {
		return data.task_id || data.taskId;
	}

	async function startItinerary(place) {
		if (!place) {
			addMessage(
				'Search a destination on the map first, then ask for an itinerary.',
				'assistant',
			);
			return;
		}
		addMessage('Plan a 1-day itinerary for ' + place + '.', 'user');
		const typingEl = addMessage(
			'Researching ' + place + ' (Wikipedia, then the local model)...',
			'assistant typing',
			{ delay: 100 },
		);
		typingEl.classList.add('typing-indicator');

		if (typeof window.anime === 'function' && !REDUCED_MOTION) {
			const dots = typingEl.querySelector('span');
			if (dots) {
				let dotCount = 0;
				const interval = setInterval(() => {
					if (!document.body.contains(typingEl)) {
						clearInterval(interval);
						return;
					}
					dotCount = (dotCount + 1) % 4;
					dots.textContent = 'Researching ' + place + ' ' + '.'.repeat(dotCount);
				}, 500);
				typingEl.dataset.dotInterval = interval;
			}
		}

		let data;
		try {
			data = await postForm(itineraryUrl, { place: place });
		} catch (error) {
			if (typingEl.dataset.dotInterval) clearInterval(typingEl.dataset.dotInterval);
			typingEl.remove();
			addMessage(error.message, 'assistant');
			return;
		}
		pollTask(taskIdFix(data), typingEl, function (result) {
			if (typingEl.dataset.dotInterval) clearInterval(typingEl.dataset.dotInterval);
			if (result.error) {
				addMessage(result.error, 'assistant', { delay: 50 });
				setTimeout(() => playClass(chatMessages.lastElementChild, 'animate__shakeX'), 100);
				return;
			}
			if (result.facts) {
				addMessage('About ' + place + ': ' + result.facts, 'assistant', { delay: 50 });
			}
			addMessage(
				result.itinerary || 'No itinerary came back.',
				'assistant',
				{ delay: 150 },
			);
		});
	}

	function startNavigationHelp(place) {
		const from =
			typeof start !== 'undefined' && start && start.name
				? start.name
				: 'your start point';
		const to = place || 'your destination';
		askQuestion(
			'Give short driving navigation tips from ' +
				from +
				' to ' +
				to +
				': key route, road conditions, and one safety tip. Keep it to 3-4 sentences.',
			to,
		);
	}

	// Suggestion buttons with rich interactions
	document.querySelectorAll('.suggestion-btn').forEach(function (btn) {
		btn.addEventListener('click', function () {
			const place = currentPlaceName();
			const kind = btn.dataset.suggestion;

			// Button press feedback (anime.js)
			animeSafe({
				targets: btn,
				scale: [1, 0.92, 1],
				duration: 150,
				easing: 'easeOutQuad',
			});

			// Ripple effect (animate.css)
			playClass(btn, 'animate__heartBeat');

			if (kind === 'about') {
				if (!place) {
					addMessage(
						'Search a destination on the map first, then ask about it.',
						'assistant',
					);
					return;
				}
				askQuestion('Tell me about ' + place + '.', place);
			} else if (kind === 'navigate') {
				startNavigationHelp(place);
			} else if (kind === 'itinerary') {
				startItinerary(place);
			}
		});

		// Hover/touch feedback
		btn.addEventListener('mouseenter', function () {
			if (!REDUCED_MOTION && typeof window.anime === 'function') {
				window.anime({
					targets: btn,
					translateY: [-2],
					duration: 150,
					easing: 'easeOutQuad',
				});
			}
		});
		btn.addEventListener('mouseleave', function () {
			if (!REDUCED_MOTION && typeof window.anime === 'function') {
				window.anime({
					targets: btn,
					translateY: [0],
					duration: 200,
					easing: 'easeOutQuad',
				});
			}
		});
	});

	chatForm.addEventListener('submit', function (e) {
		e.preventDefault();
		const question = chatInput.value.trim();
		if (!question) {
			playClass(chatInput, 'animate__shakeX');
			return;
		}
		askQuestion(question, currentPlaceName());
	});

	// Input focus animations - use CSS class instead of anime for box-shadow (CSS vars don't animate well)
	chatInput.addEventListener('focus', function () {
		this.classList.add('input-focused');
	});
	chatInput.addEventListener('blur', function () {
		this.classList.remove('input-focused');
	});

	// ESC to close with animation
	document.addEventListener('keydown', function (e) {
		if (e.key === 'Escape' && chatModal && !chatModal.hidden) {
			const alpineComponent = document.querySelector('#chatbot');
			if (alpineComponent && alpineComponent.__x) {
				alpineComponent.__x.getUnobservedData().open = false;
			}
		}
	});
})();