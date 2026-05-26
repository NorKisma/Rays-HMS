/**
 * Rays HMS API Service Layer
 * A clean, robust client for standard multi-tenant REST API interaction.
 * Handles authentication error catching, request rate limit retry concepts,
 * and structured JSON formatting.
 */

const RaysAPI = {
    // Helper to send HTTP requests with consistent headers and response mapping
    async _request(url, options = {}) {
        const defaults = {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest' // To notify Flask endpoints of AJAX
            }
        };

        const config = {
            ...defaults,
            ...options,
            headers: {
                ...defaults.headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, config);

            // Handle unauthorized globally
            if (response.status === 401) {
                console.error("Session expired. Redirecting to login...");
                window.location.href = '/auth/login?next=' + encodeURIComponent(window.location.pathname);
                return { success: false, error: "Unauthorized" };
            }

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                return {
                    success: false,
                    error: errData.message || `HTTP error! status: ${response.status}`
                };
            }

            return await response.json();
        } catch (error) {
            console.error(`RaysAPI Error requesting ${url}:`, error);
            return { success: false, error: error.message };
        }
    },

    // ----------------------------------------------------
    // Dashboard Real-time Endpoints
    // ----------------------------------------------------
    async getDashboardStats() {
        return this._request('/api/v1/dashboard/stats');
    },

    async getRecentPatients() {
        return this._request('/api/v1/dashboard/recent-patients');
    },

    async getRevenueChart() {
        return this._request('/api/v1/dashboard/revenue-chart');
    },

    async getDepartmentLoad() {
        return this._request('/api/v1/dashboard/department-load');
    },

    async getActivityFeed() {
        return this._request('/api/v1/dashboard/activity-feed');
    },

    // ----------------------------------------------------
    // Patients Endpoints
    // ----------------------------------------------------
    async getPatients(params = {}) {
        const url = new URL('/api/v1/patients', window.location.origin);
        Object.keys(params).forEach(key => {
            if (params[key] !== undefined && params[key] !== null) {
                url.searchParams.append(key, params[key]);
            }
        });
        return this._request(url.toString());
    },

    // ----------------------------------------------------
    // Appointments Endpoints
    // ----------------------------------------------------
    async getAppointments(params = {}) {
        const url = new URL('/api/v1/appointments', window.location.origin);
        Object.keys(params).forEach(key => {
            if (params[key] !== undefined && params[key] !== null) {
                url.searchParams.append(key, params[key]);
            }
        });
        return this._request(url.toString());
    }
};

// Export to window context for global use in page-specific scripts
window.RaysAPI = RaysAPI;
