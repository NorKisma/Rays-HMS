document.addEventListener("DOMContentLoaded", function () {
    console.log("Rays HMS Loaded ✅");
    console.log("UI Controls Initialized (Sidebar & Theme Toggle) ✅");

    /* =======================================
        HELPER FUNCTION: TOAST NOTIFICATIONS
    ======================================= */
    /**
     * Shows a Bootstrap Toast notification.
     * @param {string} message - The message to display.
     * @param {string} type - The toast background type (info, success, danger, etc.).
     */
    function showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;

        const bgClass = type === 'error' ? 'danger' : type;
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-bg-${bgClass} border-0 mb-2`;
        toast.role = 'alert';
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>`;

        toastContainer.appendChild(toast);

        // Using a 4-second delay for consistency
        const bsToast = new bootstrap.Toast(toast, { delay: 4000 }); 
        bsToast.show();

        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    // Make the unified showToast function globally available
    window.showToast = showToast;

    /* =======================================
        1. FORM VALIDATION (Bootstrap)
    ======================================= */
    const forms = document.querySelectorAll('form.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                showToast("Please fill all required fields!", "danger");
            }
            form.classList.add('was-validated');
        });
    });

    /* =======================================
        2. INITIALIZE DATA TABLES 
    ======================================= */
    if (typeof $ !== 'undefined' && $.fn.DataTable) {
        // Standard DataTable Initialization (for .datatable class)
        $('.datatable').DataTable({
            pageLength: 10,
            lengthMenu: [5, 10, 25, 50, 100],
            ordering: true,
            responsive: true,
            autoWidth: false,
            searching: true,
            language: {
                search: "🔍 Search:",
                lengthMenu: "Show _MENU_ entries per page",
                paginate: { previous: "&laquo;", next: "&raquo;" },
                info: "Showing _START_ to _END_ of _TOTAL_ entries"
            }
        });

        // Specific DataTable for #userTable
        $('#userTable').DataTable({
            "paging": false, 
            "info": false,
            "searching": false, 
            "columnDefs": [{ "orderable": false, "targets": 4 }], 
        });
    } else {
        console.warn("DataTables library not loaded.");
    }
    
    /* =======================================
        3. PROCESS SERVER-SIDE FLASH MESSAGES
    ======================================= */
    const flashDiv = document.getElementById('flash-messages');
    if(flashDiv){
        Array.from(flashDiv.children).forEach(div => {
            showToast(div.dataset.message, div.dataset.category);
        });
    }

    /* =======================================
        4. CONFIRM DELETE MODAL LOGIC (AJAX)
    ======================================= */
    let deleteUrl = null; 
    let deleteRowId = null;
    
    const deleteModalElement = document.getElementById('deleteModal');
    if (deleteModalElement) {
        const deleteModal = new bootstrap.Modal(deleteModalElement);
        // Get CSRF Token (NOTE: This variable uses Jinja syntax and MUST be set in your template)
        const csrfToken = "{{ csrf_token() }}"; 

        window.confirmDelete = function(id, name, formSelector) {
            const form = document.querySelector(formSelector);
            if (form && form.dataset.baseAction) {
                form.action = form.dataset.baseAction.replace('ID', id); 
            }
            document.getElementById('deleteItemName').textContent = name; 
            deleteModal.show();
        }

        document.body.addEventListener('click', function(e) {
            if(e.target.closest('.delete-btn')) {
                const btn = e.target.closest('.delete-btn');
                deleteRowId = btn.dataset.userId; 
                deleteUrl = btn.dataset.deleteUrl; 
                const name = btn.dataset.userName;
                
                document.getElementById('deleteItemName').textContent = name; 
                deleteModal.show();
            }
        });

        document.getElementById('confirmDeleteBtn').addEventListener('click', function() {
            if(!deleteUrl) {
                showToast('Delete URL not set.', 'danger');
                deleteModal.hide();
                return;
            }

            fetch(deleteUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken 
                }
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().catch(() => {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                if(data.status === 'success'){
                    const row = document.getElementById(`user-${deleteRowId}`);
                    if(row) row.remove();
                    showToast(data.message, 'success');
                } else {
                    showToast(data.message || 'Deletion failed due to a server issue.', 'danger');
                }
            })
            .catch(error => {
                console.error('Fetch Error:', error);
                showToast('An unexpected error occurred while deleting.', 'danger');
            })
            .finally(() => {
                deleteModal.hide();
            });
        });
    }


    /* =======================================
        5. SIDEBAR TOGGLE & RESPONSIVENESS
    ======================================= */
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const toggleBtn = document.getElementById('sidebarToggle'); 
    const navbarToggle = document.getElementById('navbarSidebarToggle'); 
    const overlay = document.getElementById('overlay'); 

    function toggleSidebar() {
        if (!sidebar || !mainContent) return; 

        if (window.innerWidth <= 768) {
            // Mobile view
            sidebar.classList.toggle('open');
            if (overlay) overlay.classList.toggle('active');
        } else {
            // Desktop view
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');
        }
    }

    if (toggleBtn) toggleBtn.addEventListener('click', toggleSidebar);
    if (navbarToggle) navbarToggle.addEventListener('click', toggleSidebar);

    if (overlay) {
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        });
    }

    /* =======================================
        6. THEME TOGGLE (LIGHT/DARK MODE)
    ======================================= */
    const themeToggleBtn = document.getElementById("themeToggle");
    const themeIcon = document.getElementById("themeIcon");
    const navbar = document.getElementById("mainNavbar");

    function applyTheme(theme) {
        if (!themeIcon || !navbar || !themeToggleBtn) return; 

        if (theme === "dark") {
            document.body.classList.add("dark-mode");
            themeIcon.classList.replace("fa-moon", "fa-sun");
            
            // Adjust Navbar Classes for Dark Mode
            navbar.classList.add("navbar-dark", "bg-dark");
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
            
            document.body.classList.toggle("dark-mode", newTheme === "dark"); 
            
            localStorage.setItem("theme", newTheme);
            applyTheme(newTheme);
        });
    }
});