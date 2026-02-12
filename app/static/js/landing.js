/* landing.js — dark mode, mobile menu, navbar scroll, AOS + Swiper inits */

/* ---------- Helpers & DOM ---------- */
const body = document.documentElement;
const toggleBtn = document.querySelector(".dark-toggle");
const navbar = document.querySelector(".navbar");
const navLinks = document.querySelector(".nav-links");
const navToggle = document.querySelector(".nav-toggle");

/* ---------- THEME: detect & persist ---------- */
(function initTheme() {
    try {
        const saved = localStorage.getItem("theme");
        const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;

        if (saved === "dark" || (!saved && prefersDark)) {
            document.body.classList.add("dark");
            if (toggleBtn) toggleBtn.textContent = "☀";
        } else {
            document.body.classList.remove("dark");
            if (toggleBtn) toggleBtn.textContent = "🌙";
        }
    } catch (e) {
        console.warn("Theme init error", e);
    }
})();

function toggleDarkMode() {
    const isDark = document.body.classList.toggle("dark");
    try {
        localStorage.setItem("theme", isDark ? "dark" : "light");
    } catch (e) { console.warn("Unable to save theme", e); }
    if (toggleBtn) toggleBtn.textContent = isDark ? "☀" : "🌙";

    // subtle click animation
    if (toggleBtn) {
        toggleBtn.classList.add("clicked");
        setTimeout(()=> toggleBtn.classList.remove("clicked"), 260);
    }
}

/* ---------- MOBILE MENU ---------- */
function toggleMenu() {
    if (!navLinks) return;
    navLinks.classList.toggle("open");
}

/* close mobile menu when clicking outside (helpful) */
document.addEventListener("click", (e) => {
    if (!navLinks) return;
    if (navLinks.classList.contains("open")) {
        const isClickInside = navLinks.contains(e.target) || e.target.closest(".nav-toggle");
        if (!isClickInside) navLinks.classList.remove("open");
    }
});

/* ---------- NAVBAR SCROLL ---------- */
window.addEventListener("scroll", () => {
    if (!navbar) return;
    if (window.scrollY > 40) {
        navbar.style.transform = "translateX(-50%) translateY(-6px)";
        navbar.style.boxShadow = "0 18px 40px rgba(6,95,70,0.08)";
    } else {
        navbar.style.transform = "translateX(-50%) translateY(0)";
        navbar.style.boxShadow = "";
    }
});

/* ---------- AOS init ---------- */
document.addEventListener("DOMContentLoaded", () => {
    if (window.AOS) {
        AOS.init({ duration: 800, easing: "ease-out-quart", once: true });
    }

    /* ---------- Swiper init ---------- */
    if (window.Swiper) {
        try {
            if (document.querySelector(".featureSwiper")) {
                new Swiper(".featureSwiper", {
                    slidesPerView: 3,
                    spaceBetween: 20,
                    pagination: { el: ".swiper-pagination", clickable: true },
                    breakpoints: {
                        0: { slidesPerView: 1 },
                        640: { slidesPerView: 2 },
                        1024: { slidesPerView: 3 }
                    }
                });
            }

            if (document.querySelector(".testimonialSwiper")) {
                new Swiper(".testimonialSwiper", {
                    slidesPerView: 1,
                    spaceBetween: 20,
                    pagination: { el: ".swiper-pagination", clickable: true },
                    autoplay: { delay: 5500, disableOnInteraction: true },
                    loop: true
                });
            }
        } catch (e) { console.warn("Swiper init error", e); }
    }
});

/* expose toggleMenu so HTML onClick can call it */
window.toggleMenu = toggleMenu;
window.toggleDarkMode = toggleDarkMode;
