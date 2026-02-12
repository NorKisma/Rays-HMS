document.addEventListener("DOMContentLoaded", () => {
    // Ensure Chart.js is available before running chart initialization
    if (typeof Chart === 'undefined') {
        console.error("Chart.js library not found. Charts will not be initialized.");
    }

    /* =======================================
       1. MONTHLY REVENUE CHART (Line Chart)
    ======================================= */
    const revenueCtx = document.getElementById("revenueChart");
    if (revenueCtx && typeof Chart !== 'undefined') {
        new Chart(revenueCtx, {
            type: "line",
            data: {
                // Assumes revenue_labels and revenue_values are globally available
                labels: revenue_labels || [], 
                datasets: [{
                    label: "Revenue",
                    data: revenue_values || [],
                    borderColor: "rgba(54,162,235,1)",
                    backgroundColor: "rgba(54,162,235,0.2)",
                    tension: 0.3, // Smooth curve
                    fill: true
                }]
            },
            options: { 
                responsive: true, 
                plugins: { 
                    legend: { 
                        display: true, 
                        position: 'top' 
                    } 
                } 
            }
        });
    }

    /* =======================================
       2. SALES CHART (Bar Chart)
    ======================================= */
    const salesCtx = document.getElementById("salesChart");
    if (salesCtx && typeof Chart !== 'undefined') {
        new Chart(salesCtx, {
            type: "bar",
            data: {
                // Assumes sales_labels and sales_values are globally available
                labels: sales_labels || [], 
                datasets: [{
                    label: "Sales",
                    data: sales_values || [],
                    backgroundColor: "rgba(255,99,132,0.7)"
                }]
            },
            options: { 
                responsive: true, 
                plugins: { 
                    legend: { 
                        display: true, 
                        position: 'top' 
                    } 
                } 
            }
        });
    }

    /* =======================================
       3. DATATABLES FOR INVOICES
    ======================================= */
    // Ensure jQuery and DataTables are loaded
    if (typeof $ !== 'undefined' && $.fn.DataTable) {
        const invoicesTable = $("#invoicesTable").DataTable({ 
            // Order by the 3rd column (index 2, often date/amount) descending by default
            order: [[2, 'desc']], 
            pageLength: 10 
        });

        /* =======================================
           4. INVOICE FILTERING BY STATUS (Using DataTables)
        ======================================= */
        const filterButtons = document.querySelectorAll(".summary-card");
        filterButtons.forEach(btn => {
            btn.addEventListener("click", () => {
                const filterValue = btn.getAttribute("data-filter");
                
                // Clear any existing DataTables search filter first
                invoicesTable.search('').columns().search('').draw();

                if (filterValue !== "all") {
                    // Apply filter to the status column (assuming status is in the 4th column, index 3)
                    // NOTE: You may need to adjust the column index (e.g., [3]) based on your HTML structure.
                    // This implementation uses jQuery/DOM manipulation on hidden/shown rows instead of DataTables API:
                    invoicesTable.rows().every(function() {
                        const rowNode = $(this.node());
                        // Assumes the status is stored as a data-status attribute on the <tr> tag
                        const status = rowNode.data("status"); 

                        if (status === filterValue) { 
                            rowNode.show(); 
                        } else { 
                            rowNode.hide(); 
                        }
                    });
                    
                    // Manually re-draw the table to update display/info (optional, based on filtering method)
                    // invoicesTable.draw();
                } else {
                    // If 'all', show all rows 
                    invoicesTable.rows().every(function() {
                        $(this.node()).show();
                    });
                    // Re-draw to ensure DataTables knows all rows are visible
                    invoicesTable.draw(); 
                }
            });
        });
    } else {
        console.warn("jQuery or DataTables library not found. Table filtering disabled.");
    }


    /* =======================================
       5. CARD HOVER EFFECT (JS implementation)
    ======================================= */
    // NOTE: This effect is often handled better and cleaner with pure CSS 
    // (as seen in your dashboard.css), but keeping the JS implementation for completeness.
    document.querySelectorAll(".dash-card").forEach(card => {
        card.addEventListener("mouseenter", () => card.style.transform = "translateY(-5px)");
        card.addEventListener("mouseleave", () => card.style.transform = "translateY(0)");
    });
});