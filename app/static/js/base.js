document.addEventListener("DOMContentLoaded", function () {
    console.log("UI Controls Initialized (Sidebar & Theme Toggle) ✅");
    
    /* =======================================
       1. SIDEBAR TOGGLE & RESPONSIVENESS
    ======================================= */
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const toggleBtn = document.getElementById('sidebarToggle'); // Button outside sidebar
    const navbarToggle = document.getElementById('navbarSidebarToggle'); // Button inside navbar
    const overlay = document.getElementById('overlay'); // Mobile overlay

    /**
     * Toggles the sidebar state based on screen size.
     * On desktop: Collapses/expands the sidebar.
     * On mobile: Opens/closes the sidebar and activates/deactivates the overlay.
     */
    function toggleSidebar() {
        if (!sidebar || !mainContent) return; // Exit if necessary elements aren't found
       if (window.innerWidth <= 768) {
            // Mobile view: Full slide-out menu with overlay
            sidebar.classList.toggle('open');
            if (overlay) overlay.classList.toggle('active');
        } else {
            // Desktop view: Collapsed/expanded state
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');
        }
    }

    // Attach listeners to the toggle buttons
    if (toggleBtn) toggleBtn.addEventListener('click', toggleSidebar);
    if (navbarToggle) navbarToggle.addEventListener('click', toggleSidebar);

    // Close sidebar when clicking the mobile overlay
    if (overlay) {
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        });
    }

    /* =======================================
       2. THEME TOGGLE (LIGHT/DARK MODE)
    ======================================= */
    const themeToggleBtn = document.getElementById("themeToggle");
    const themeIcon = document.getElementById("themeIcon");
    const navbar = document.getElementById("mainNavbar");

    /**
     * Applies the specified theme to the document body and UI elements.
     * @param {string} theme - The theme name ('light' or 'dark').
     */
    function applyTheme(theme) {
        if (!themeIcon || !navbar || !themeToggleBtn) return; // Exit if necessary elements aren't found

        if (theme === "dark") {
            document.body.classList.add("dark-mode");
            themeIcon.classList.replace("fa-moon", "fa-sun");
            
            // Adjust Navbar Classes for Dark Mode
            navbar.classList.add("navbar-dark", "bg-dark");
            // NOTE: 'navbar-custom' is a gradient in your CSS, so it's removed for standard dark background
            navbar.classList.remove("navbar-custom", "text-white"); 
            themeToggleBtn.classList.replace("btn-outline-light", "btn-outline-secondary");
        } else {
            document.body.classList.remove("dark-mode");
            themeIcon.classList.replace("fa-sun", "fa-moon");
            
            // Adjust Navbar Classes for Light Mode
            navbar.classList.remove("bg-dark", "navbar-dark");
            navbar.classList.add("navbar-custom", "text-white");
            themeToggleBtn.classList.replace("btn-outline-secondary", "btn-outline-light");
        }
    }

    // Load saved theme on initial page load
    const savedTheme = localStorage.getItem("theme") || "light";
    applyTheme(savedTheme);

    // Toggle theme on click
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            const isDark = document.body.classList.contains("dark-mode");
            const newTheme = isDark ? "light" : "dark";
            
            // Toggle the class immediately before calling applyTheme
            document.body.classList.toggle("dark-mode", newTheme === "dark"); 
            
            localStorage.setItem("theme", newTheme);
            applyTheme(newTheme);
        });
    }
});