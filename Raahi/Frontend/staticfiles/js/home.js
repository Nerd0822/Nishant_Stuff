// Home page — rich orchestrated entrance with anime.js
// Counters, staggered reveals, scroll-triggered animations, parallax

(function () {
	'use strict';

	// Respect reduced motion
	const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

	// ============================================================
	// 1. HERO ENTRANCE SEQUENCE
	// ============================================================
	if (typeof window.anime === 'function' && !REDUCED_MOTION) {
		const heroElements = [
			{ sel: '.home-hero h1', translateY: 30, delay: 0 },
			{ sel: '.hero-tagline', translateY: 24, delay: 150 },
			{ sel: '.home-cta', translateY: 20, delay: 300 },
			{ sel: '.hero-stats', translateY: 20, delay: 450 },
			{ sel: '.hero-scroll-indicator', translateY: 10, delay: 600 },
		];

		window.anime.timeline({ easing: 'easeOutCubic' })
			.add({
				targets: '.home-hero',
				opacity: [0, 1],
				duration: 100,
			})
			.add({
				targets: heroElements.map(h => h.sel).join(', '),
				opacity: [0, 1],
				translateY: function (el, i) {
					const cfg = heroElements.find(h => el.matches(h.sel));
					return cfg ? [cfg.translateY, 0] : [20, 0];
				},
				duration: 700,
				delay: function (el, i) {
					const cfg = heroElements.find(h => el.matches(h.sel));
					return cfg ? cfg.delay : 0;
				},
				easing: 'easeOutExpo',
			}, 0);
	} else {
		// Instant show for reduced motion
		document.querySelectorAll('.home-hero > *, .feature-card, .cta-banner').forEach((el) => {
			el.style.opacity = '';
			el.style.transform = '';
		});
		// Set counters to final values
		document.querySelectorAll('[data-count]').forEach((el) => {
			el.textContent = el.dataset.count;
		});
	}

	// ============================================================
	// 2. ANIMATED COUNTERS (IntersectionObserver)
	// ============================================================
	function animateCounter(el) {
		const target = parseInt(el.dataset.count, 10);
		const duration = 1800;
		const startTime = performance.now();

		function step(now) {
			const progress = Math.min((now - startTime) / duration, 1);
			// Ease out cubic
			const eased = 1 - Math.pow(1 - progress, 3);
			const current = Math.floor(eased * target);
			el.textContent = current.toLocaleString();
			if (progress < 1) {
				requestAnimationFrame(step);
			} else {
				el.textContent = target.toLocaleString();
			}
		}
		requestAnimationFrame(step);
	}

	const counterObserver = new IntersectionObserver((entries) => {
		entries.forEach((entry) => {
			if (entry.isIntersecting) {
				animateCounter(entry.target);
				counterObserver.unobserve(entry.target);
			}
		});
	}, { threshold: 0.5, rootMargin: '0px 0px -50px 0px' });

	document.querySelectorAll('[data-count]').forEach((el) => {
		el.textContent = '0';
		counterObserver.observe(el);
	});

	// ============================================================
	// 3. SCROLL REVEAL (IntersectionObserver + CSS animations)
	// ============================================================
	const revealObserver = new IntersectionObserver((entries) => {
		entries.forEach((entry) => {
			if (entry.isIntersecting) {
				entry.target.classList.add('scroll-reveal');
				revealObserver.unobserve(entry.target);
			}
		});
	}, { threshold: 0.15, rootMargin: '0px 0px -50px 0px' });

	// Observe all elements with data-scroll-reveal
	document.querySelectorAll('[data-scroll-reveal]').forEach((el) => {
		revealObserver.observe(el);
	});

	// Also observe feature cards for staggered reveal
	const featureObserver = new IntersectionObserver((entries) => {
		entries.forEach((entry, i) => {
			if (entry.isIntersecting) {
				entry.target.style.animationDelay = `${i * 100}ms`;
				entry.target.classList.add('scroll-reveal');
				featureObserver.unobserve(entry.target);
			}
		});
	}, { threshold: 0.15, rootMargin: '0px 0px -50px 0px' });

	document.querySelectorAll('.feature-card').forEach((card) => {
		card.style.opacity = '0';
		card.style.transform = 'translateY(30px)';
		featureObserver.observe(card);
	});

	// CTA banner reveal
	const ctaObserver = new IntersectionObserver((entries) => {
		entries.forEach((entry) => {
			if (entry.isIntersecting) {
				entry.target.classList.add('scroll-reveal');
				ctaObserver.unobserve(entry.target);
			}
		});
	}, { threshold: 0.25 });

	const ctaBanner = document.querySelector('.cta-banner');
	if (ctaBanner) {
		ctaBanner.style.opacity = '0';
		ctaBanner.style.transform = 'scale(0.95)';
		ctaObserver.observe(ctaBanner);
	}

	// ============================================================
	// 4. PARALLAX EFFECT ON HERO BACKGROUND
	// ============================================================
	if (!REDUCED_MOTION && typeof window.anime === 'function') {
		let ticking = false;
		const heroBg = document.querySelector('.home-hero::before');
		
		function updateParallax() {
			const scrollY = window.scrollY;
			const hero = document.querySelector('.home-hero');
			if (hero && scrollY < window.innerHeight * 1.5) {
				// Parallax on the pseudo-element via CSS custom property
				const offset = scrollY * 0.3;
				hero.style.setProperty('--parallax-offset', `${offset}px`);
			}
			ticking = false;
		}

		window.addEventListener('scroll', function () {
			if (!ticking) {
				window.requestAnimationFrame(updateParallax);
				ticking = true;
			}
		}, { passive: true });

		// Also apply subtle parallax to feature card backgrounds
		const featureCards = document.querySelectorAll('.feature-card');
		function updateCardParallax() {
			const scrollY = window.scrollY;
			featureCards.forEach((card) => {
				const rect = card.getBoundingClientRect();
				const cardCenter = rect.top + rect.height / 2;
				const viewportCenter = window.innerHeight / 2;
				const distance = cardCenter - viewportCenter;
				const offset = distance * 0.15;
				
				const bg = card.querySelector('.feature-bg');
				if (bg && Math.abs(offset) < 100) {
					bg.style.transform = `translateY(${offset}px)`;
				}
			});
			ticking = false;
		}

		// Use single scroll listener for both
		window.addEventListener('scroll', function () {
			if (!ticking) {
				window.requestAnimationFrame(() => {
					updateParallax();
					updateCardParallax();
					ticking = true;
				});
				ticking = true;
			}
		}, { passive: true });
	}

	// ============================================================
	// 5. INTERACTIVE HOVER EFFECTS
	// ============================================================
	// Feature card hover
	document.querySelectorAll('.feature-card').forEach((card) => {
		card.addEventListener('mouseenter', function () {
			if (!REDUCED_MOTION && typeof window.anime === 'function') {
				window.anime({
					targets: this,
					translateY: [-8],
					boxShadow: ['var(--shadow-medium)', 'var(--shadow-strong)'],
					duration: 300,
					easing: 'easeOutQuad',
				});
				const icon = this.querySelector('.feature-icon');
				if (icon) {
					window.anime({
						targets: icon,
						rotate: [0, 6, -6, 0],
						scale: [1, 1.1, 1],
						duration: 600,
						easing: 'easeOutElastic(1, .8)',
					});
				}
				const bg = this.querySelector('.feature-bg');
				if (bg) {
					window.anime({
						targets: bg,
						filter: ['brightness(0.35) saturate(1.1)', 'brightness(0.5) saturate(1.2)'],
						scale: [1, 1.05],
						duration: 400,
						easing: 'easeOutQuad',
					});
				}
			}
		});
		card.addEventListener('mouseleave', function () {
			if (!REDUCED_MOTION && typeof window.anime === 'function') {
				window.anime({
					targets: this,
					translateY: [0],
					boxShadow: 'var(--shadow-soft)',
					duration: 400,
					easing: 'easeOutQuad',
				});
				const bg = this.querySelector('.feature-bg');
				if (bg) {
					window.anime({
						targets: bg,
						filter: 'brightness(0.5) saturate(1.2)',
						scale: 1,
						duration: 600,
						easing: 'easeOutQuad',
					});
				}
			}
		});
	});

	// CTA button hover
	const ctaBtn = document.querySelector('.cta-banner .btn');
	if (ctaBtn) {
		ctaBtn.addEventListener('mouseenter', function () {
			if (!REDUCED_MOTION && typeof window.anime === 'function') {
				window.anime({
					targets: this,
					scale: [1, 1.03],
					boxShadow: ['0 4px 20px var(--shadow-primary)', '0 8px 32px var(--shadow-primary)'],
					duration: 200,
				});
			}
		});
		ctaBtn.addEventListener('mouseleave', function () {
			if (!REDUCED_MOTION && typeof window.anime === 'function') {
				window.anime({
					targets: this,
					scale: 1,
					boxShadow: '0 4px 20px var(--shadow-primary)',
					duration: 300,
				});
			}
		});
	}

	// ============================================================
	// 6. SMOOTH SCROLL FOR SCROLL INDICATOR
	// ============================================================
	const scrollIndicator = document.querySelector('.hero-scroll-indicator');
	if (scrollIndicator) {
		scrollIndicator.addEventListener('click', function () {
			const featuresSection = document.querySelector('.features');
			if (featuresSection) {
				featuresSection.scrollIntoView({ behavior: 'smooth' });
			}
		});
	}

	// ============================================================
	// 7. SAFETY NET
	// ============================================================
	setTimeout(() => {
		document.querySelectorAll('.home-hero > *, .feature-card, .cta-banner').forEach((el) => {
			el.style.opacity = '';
			el.style.transform = '';
		});
	}, 4000);
})();