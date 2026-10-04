/**
 * CarbonLens — Progressive Enhancements & Interactive Visualization Engine
 * Features:
 *  - Interactive Chart.js visualizations with tooltips, legend toggling & hover highlights
 *  - Modal zoom & expand capability for high-resolution analysis
 *  - Toggle between interactive canvas and publication-grade static charts
 *  - Header profile dropdown menu & dismiss interactions
 *  - Drag-and-drop dataset upload handler
 *  - Dynamic What-If simulation slider readouts
 *  - Account type selector tab toggles
 */

document.addEventListener("DOMContentLoaded", function () {
    // ---------------------------------------------------------------------
    // 1. Drag and Drop Upload Handler
    // ---------------------------------------------------------------------
    const dropzone = document.getElementById("upload-dropzone");
    const fileInput = document.getElementById("file-input");
    const fileFeedback = document.getElementById("file-selected-name");

    if (dropzone && fileInput) {
        ["dragenter", "dragover"].forEach((eventName) => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add("dragover");
            });
        });

        ["dragleave", "drop"].forEach((eventName) => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove("dragover");
            });
        });

        dropzone.addEventListener("drop", (e) => {
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                updateFileName(e.dataTransfer.files[0].name);
            }
        });

        dropzone.addEventListener("click", () => {
            fileInput.click();
        });

        fileInput.addEventListener("change", () => {
            if (fileInput.files.length > 0) {
                updateFileName(fileInput.files[0].name);
            }
        });

        function updateFileName(name) {
            if (fileFeedback) {
                fileFeedback.textContent = `Selected: ${name}`;
                fileFeedback.style.display = "block";
            }
        }
    }

    // ---------------------------------------------------------------------
    // 2. What-If Simulation Sliders
    // ---------------------------------------------------------------------
    const sliders = document.querySelectorAll(".simulation-slider");
    sliders.forEach((slider) => {
        const outputTarget = document.getElementById(`${slider.id}-val`);
        if (outputTarget) {
            slider.addEventListener("input", function () {
                outputTarget.textContent = `${this.value}%`;
            });
        }
    });

    // ---------------------------------------------------------------------
    // 3. Tab switching for Registration Page
    // ---------------------------------------------------------------------
    const accountTypeSelect = document.getElementById("account_type_select");
    const orgFields = document.getElementById("organization_specific_fields");
    if (accountTypeSelect && orgFields) {
        accountTypeSelect.addEventListener("change", function () {
            if (this.value === "ORGANIZATION") {
                orgFields.style.display = "block";
            } else {
                orgFields.style.display = "none";
            }
        });
    }

    // ---------------------------------------------------------------------
    // 4. Header Profile Dropdown Toggle
    // ---------------------------------------------------------------------
    const profileBtn = document.getElementById("profileDropdownBtn");
    const profileMenu = document.getElementById("profileDropdownMenu");
    const profileWrapper = document.querySelector(".profile-dropdown-wrapper");

    if (profileBtn && profileMenu && profileWrapper) {
        profileBtn.addEventListener("click", function (e) {
            e.stopPropagation();
            const isOpen = profileWrapper.classList.contains("active");
            if (isOpen) {
                profileWrapper.classList.remove("active");
                profileBtn.setAttribute("aria-expanded", "false");
            } else {
                profileWrapper.classList.add("active");
                profileBtn.setAttribute("aria-expanded", "true");
            }
        });

        document.addEventListener("click", function (e) {
            if (!profileWrapper.contains(e.target)) {
                profileWrapper.classList.remove("active");
                profileBtn.setAttribute("aria-expanded", "false");
            }
        });

        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && profileWrapper.classList.contains("active")) {
                profileWrapper.classList.remove("active");
                profileBtn.setAttribute("aria-expanded", "false");
            }
        });
    }

    // ---------------------------------------------------------------------
    // 5. Toggle Interactive View vs Static Publication View
    // ---------------------------------------------------------------------
    const toggleButtons = document.querySelectorAll(".btn-toggle-static");
    toggleButtons.forEach((btn) => {
        btn.addEventListener("click", function () {
            const targetId = this.getAttribute("data-toggle-target");
            const interactiveWrap = document.getElementById(`wrap-interactive-${targetId}`);
            const staticWrap = document.getElementById(`wrap-static-${targetId}`);

            if (interactiveWrap && staticWrap) {
                const isInteractiveVisible = interactiveWrap.style.display !== "none";
                if (isInteractiveVisible) {
                    interactiveWrap.style.display = "none";
                    staticWrap.style.display = "flex";
                    this.textContent = "📈 Interactive View";
                    this.classList.add("active");
                } else {
                    interactiveWrap.style.display = "flex";
                    staticWrap.style.display = "none";
                    this.textContent = "📊 Toggle View";
                    this.classList.remove("active");
                }
            }
        });
    });

    // ---------------------------------------------------------------------
    // 6. Interactive Chart Zoom & Expand Modal Engine
    // ---------------------------------------------------------------------
    const modalBackdrop = document.getElementById("chartExpandModal");
    const modalTitle = document.getElementById("modalChartTitle");
    const modalSubtitle = document.getElementById("modalChartSubtitle");
    const modalCanvas = document.getElementById("modalChartCanvas");
    const modalDetails = document.getElementById("modalChartDetails");
    const closeModalBtn = document.getElementById("closeModalBtn");
    let modalChartInstance = null;

    function closeModal() {
        if (modalBackdrop) {
            modalBackdrop.style.display = "none";
            modalBackdrop.classList.remove("active");
            if (modalChartInstance) {
                modalChartInstance.destroy();
                modalChartInstance = null;
            }
            if (modalCanvas) {
                modalCanvas.style.display = "block";
            }
            // Remove any temporary modal image
            const tempImg = document.getElementById("modalChartImg");
            if (tempImg) tempImg.remove();
        }
    }

    if (closeModalBtn) {
        closeModalBtn.addEventListener("click", closeModal);
    }
    if (modalBackdrop) {
        modalBackdrop.addEventListener("click", function (e) {
            if (e.target === modalBackdrop) closeModal();
        });
    }
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && modalBackdrop && modalBackdrop.style.display !== "none") {
            closeModal();
        }
    });

    // Store active chart instances and their configurations for modal cloning
    const chartRegistry = {};

    function openModalWithChart(chartKey, title) {
        if (!modalBackdrop || !modalCanvas) return;
        const entry = chartRegistry[chartKey];
        if (!entry) return;

        modalTitle.textContent = title || entry.title || "Enlarged Visualization";
        modalSubtitle.textContent = entry.subtitle || "Interactive High-Resolution Analytics";

        // Display modal
        modalBackdrop.style.display = "flex";
        setTimeout(() => modalBackdrop.classList.add("active"), 10);

        if (modalChartInstance) {
            modalChartInstance.destroy();
            modalChartInstance = null;
        }

        const modalCtx = modalCanvas.getContext("2d");
        const clonedConfig = JSON.parse(JSON.stringify(entry.config));

        // Enhance fonts and sizing for modal view
        if (clonedConfig.options) {
            clonedConfig.options.responsive = true;
            clonedConfig.options.maintainAspectRatio = false;
            if (clonedConfig.options.plugins && clonedConfig.options.plugins.legend) {
                clonedConfig.options.plugins.legend.labels = {
                    font: { size: 13, weight: "bold" },
                    boxWidth: 16,
                    padding: 16,
                };
            }
            if (clonedConfig.options.scales) {
                Object.keys(clonedConfig.options.scales).forEach((scaleKey) => {
                    const s = clonedConfig.options.scales[scaleKey];
                    if (s.ticks) s.ticks.font = { size: 12 };
                    if (s.title) s.title.font = { size: 13, weight: "bold" };
                });
            }
        }

        modalChartInstance = new Chart(modalCtx, clonedConfig);

        if (modalDetails) {
            modalDetails.innerHTML = entry.detailsHtml || `
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                    <div><strong>Active Dataset:</strong> Verified Python Analytical Output</div>
                    <div><strong>Render Mode:</strong> High-Resolution Client-Side Engine</div>
                </div>
            `;
        }
    }

    // Expand image charts (e.g. Seaborn distribution / correlation plots)
    document.querySelectorAll(".btn-expand-image").forEach((btn) => {
        btn.addEventListener("click", function () {
            const imgSrc = this.getAttribute("data-img-src");
            const title = this.getAttribute("data-chart-title") || "Enlarged Plot";

            if (modalBackdrop && imgSrc) {
                modalTitle.textContent = title;
                modalSubtitle.textContent = "High-Resolution Seaborn Statistical Plot";

                if (modalCanvas) modalCanvas.style.display = "none";
                const tempImg = document.getElementById("modalChartImg");
                if (tempImg) tempImg.remove();

                const img = document.createElement("img");
                img.id = "modalChartImg";
                img.src = imgSrc;
                img.style.maxWidth = "100%";
                img.style.maxHeight = "480px";
                img.style.objectFit = "contain";
                img.style.margin = "0 auto";
                img.style.display = "block";
                img.style.borderRadius = "4px";

                modalCanvas.parentElement.appendChild(img);

                if (modalDetails) {
                    modalDetails.innerHTML = `
                        <div><strong>Statistical Source:</strong> Computed via Seaborn and Pandas EDA Pipeline.</div>
                    `;
                }

                modalBackdrop.style.display = "flex";
                setTimeout(() => modalBackdrop.classList.add("active"), 10);
            }
        });
    });

    // Expand button clicks for interactive Chart.js charts
    document.querySelectorAll(".btn-expand-chart").forEach((btn) => {
        btn.addEventListener("click", function () {
            const chartTarget = this.getAttribute("data-chart-target");
            const chartTitle = this.getAttribute("data-chart-title");
            openModalWithChart(chartTarget, chartTitle);
        });
    });

    // ---------------------------------------------------------------------
    // 7. Interactive Visualization Engine Initialization
    // ---------------------------------------------------------------------
    if (typeof Chart === "undefined") {
        console.warn("Chart.js is not loaded. Skipping interactive visualization initialization.");
        return;
    }

    // CarbonLens Scientific Theme Palette
    const THEME = {
        forest: "#1B4332",
        forestDark: "#143527",
        sageDeep: "#2D6A4F",
        accentGreen: "#40916C",
        mintSage: "#52B788",
        mint: "#74C69D",
        mintSoft: "#95D5B2",
        gold: "#D97706",
        charcoal: "#1F2421",
        muted: "#555E57",
        grid: "rgba(0, 0, 0, 0.06)",
        cardBg: "#FFFFFF",
    };

    const PALETTE = [
        THEME.forest,
        THEME.sageDeep,
        THEME.accentGreen,
        THEME.mintSage,
        THEME.mint,
        THEME.mintSoft,
    ];

    // Shared Chart.js defaults
    Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    Chart.defaults.color = THEME.charcoal;
    Chart.defaults.plugins.tooltip.backgroundColor = "rgba(20, 53, 39, 0.94)";
    Chart.defaults.plugins.tooltip.titleColor = "#FFFFFF";
    Chart.defaults.plugins.tooltip.bodyColor = "#E8F5E9";
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 6;
    Chart.defaults.plugins.tooltip.boxPadding = 4;
    Chart.defaults.plugins.tooltip.usePointStyle = true;

    // =====================================================================
    // 8. Individual Dashboard Interactive Visualizations
    // =====================================================================
    const indDataEl = document.getElementById("individual-calc-data");
    if (indDataEl) {
        try {
            const indData = JSON.parse(indDataEl.textContent);
            const breakdown = indData.breakdown || {};

            // -----------------------------------------------------------------
            // Chart 1: Daily Emissions by Activity (g CO2e) — Horizontal Bar
            // -----------------------------------------------------------------
            const c1 = document.getElementById("canvas-ind-act-co2");
            if (c1) {
                const activityLabels = [
                    "Laptop Usage",
                    "Smartphone Usage",
                    "Video Streaming",
                    "Emails Sent",
                    "AI Queries",
                ];
                const actKeys = ["laptop", "smartphone", "streaming", "email", "ai"];
                const actGrams = actKeys.map((k) => (breakdown[k] ? breakdown[k].co2e_g || 0 : 0));
                const actPcts = actKeys.map((k) => (breakdown[k] ? breakdown[k].percentage || 0 : 0));

                const config1 = {
                    type: "bar",
                    data: {
                        labels: activityLabels,
                        datasets: [
                            {
                                label: "Daily Emissions (g CO₂e)",
                                data: actGrams,
                                backgroundColor: PALETTE.slice(0, 5),
                                borderColor: THEME.forest,
                                borderWidth: 1,
                                borderRadius: 4,
                                hoverBackgroundColor: "#52B788",
                                hoverBorderColor: "#1B4332",
                                hoverBorderWidth: 2,
                            },
                        ],
                    },
                    options: {
                        indexAxis: "y",
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: { duration: 750, easing: "easeOutQuart" },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: function (ctx) {
                                        const idx = ctx.dataIndex;
                                        const val = ctx.raw;
                                        const pct = actPcts[idx] || 0;
                                        return ` ${val.toFixed(1)} g CO₂e (${pct.toFixed(1)}% of daily total)`;
                                    },
                                },
                            },
                        },
                        scales: {
                            x: {
                                grid: { color: THEME.grid },
                                title: { display: true, text: "Emissions (g CO₂e / day)", font: { weight: "600" } },
                                beginAtZero: true,
                            },
                            y: {
                                grid: { display: false },
                                ticks: { font: { weight: "600" } },
                            },
                        },
                    },
                };

                const chart1 = new Chart(c1.getContext("2d"), config1);
                chartRegistry["ind-act-co2"] = {
                    title: "Daily Digital Carbon Emissions by Activity",
                    subtitle: "Granular breakdown in grams CO₂e computed via verified lifecycle factors.",
                    config: config1,
                    detailsHtml: `
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem;">
                            ${activityLabels
                                .map(
                                    (label, idx) => `
                                <div style="background: #FFFFFF; border: 1px solid var(--border-color); border-radius: 4px; padding: 0.6rem;">
                                    <div style="font-weight: 600; color: var(--color-forest);">${label}</div>
                                    <div style="font-size: 1.1rem; font-weight: 700; color: var(--color-sage);">${actGrams[idx].toFixed(1)} g</div>
                                    <div style="font-size: 0.75rem; color: var(--text-muted);">${actPcts[idx].toFixed(1)}% of total</div>
                                </div>
                            `
                                )
                                .join("")}
                        </div>
                    `,
                };
            }

            // -----------------------------------------------------------------
            // Chart 2: Direct Operational Electricity (kWh) — Vertical Bar
            // -----------------------------------------------------------------
            const c2 = document.getElementById("canvas-ind-energy");
            if (c2) {
                // Direct hardware activities only
                const energyLabels = ["Laptop Draw", "Smartphone Draw", "AI Compute Draw"];
                const energyKeys = ["laptop", "smartphone", "ai"];
                const energyKwh = energyKeys.map((k) => (breakdown[k] ? breakdown[k].energy_kwh || 0 : 0));

                const config2 = {
                    type: "bar",
                    data: {
                        labels: energyLabels,
                        datasets: [
                            {
                                label: "Direct Electricity (kWh / day)",
                                data: energyKwh,
                                backgroundColor: [THEME.mintSage, THEME.mint, THEME.accentGreen],
                                borderColor: THEME.sageDeep,
                                borderWidth: 1,
                                borderRadius: 4,
                                hoverBackgroundColor: THEME.forest,
                            },
                        ],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: { duration: 750, easing: "easeOutQuart" },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: function (ctx) {
                                        return ` Direct Energy: ${ctx.raw.toFixed(4)} kWh / day`;
                                    },
                                },
                            },
                        },
                        scales: {
                            y: {
                                grid: { color: THEME.grid },
                                title: { display: true, text: "Direct Energy (kWh)", font: { weight: "600" } },
                                beginAtZero: true,
                            },
                            x: {
                                grid: { display: false },
                                ticks: { font: { weight: "600" } },
                            },
                        },
                    },
                };

                const chart2 = new Chart(c2.getContext("2d"), config2);
                chartRegistry["ind-energy"] = {
                    title: "Direct Operational Electricity Consumption",
                    subtitle: "Hardware operational power draw strictly isolating measured physical devices.",
                    config: config2,
                    detailsHtml: `
                        <p style="margin-bottom: 0.5rem;"><strong>Scope Boundaries:</strong> Video streaming and email are accounted for via network/cloud lifecycle factors and do not register direct client device electricity draws.</p>
                        <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                            ${energyLabels
                                .map(
                                    (l, i) => `
                                <div style="background: #FFFFFF; border: 1px solid var(--border-color); border-radius: 4px; padding: 0.6rem 1rem;">
                                    <div style="font-size: 0.8rem; color: var(--text-muted);">${l}</div>
                                    <div style="font-size: 1.15rem; font-weight: 700; color: var(--color-forest);">${energyKwh[i].toFixed(4)} kWh</div>
                                </div>
                            `
                                )
                                .join("")}
                        </div>
                    `,
                };
            }

            // -----------------------------------------------------------------
            // Chart 3: Activity Contribution Share (%) — Donut Chart
            // -----------------------------------------------------------------
            const c3 = document.getElementById("canvas-ind-contrib");
            if (c3) {
                const contribLabels = [
                    "Laptop",
                    "Smartphone",
                    "Streaming",
                    "Email",
                    "AI Queries",
                ];
                const contribKeys = ["laptop", "smartphone", "streaming", "email", "ai"];
                const contribPcts = contribKeys.map((k) => (breakdown[k] ? breakdown[k].percentage || 0 : 0));
                const contribGrams = contribKeys.map((k) => (breakdown[k] ? breakdown[k].co2e_g || 0 : 0));

                const config3 = {
                    type: "doughnut",
                    data: {
                        labels: contribLabels,
                        datasets: [
                            {
                                data: contribPcts,
                                backgroundColor: PALETTE.slice(0, 5),
                                borderColor: "#FFFFFF",
                                borderWidth: 2,
                                hoverOffset: 12,
                            },
                        ],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: "62%",
                        animation: { animateRotate: true, duration: 800 },
                        plugins: {
                            legend: {
                                position: "bottom",
                                labels: {
                                    boxWidth: 12,
                                    padding: 14,
                                    font: { size: 11, weight: "600" },
                                },
                            },
                            tooltip: {
                                callbacks: {
                                    label: function (ctx) {
                                        const idx = ctx.dataIndex;
                                        const pct = ctx.raw;
                                        const g = contribGrams[idx] || 0;
                                        return ` ${ctx.label}: ${pct.toFixed(1)}% (${g.toFixed(1)} g CO₂e)`;
                                    },
                                },
                            },
                        },
                    },
                };

                const chart3 = new Chart(c3.getContext("2d"), config3);
                chartRegistry["ind-contrib"] = {
                    title: "Personal Digital Footprint Contribution Share",
                    subtitle: "Proportional distribution of total daily greenhouse gas emissions across digital activities.",
                    config: config3,
                    detailsHtml: `
                        <div style="font-size: 0.85rem; color: var(--text-main);">
                            Click any item in the legend above to dynamically isolate or compare selected digital activities.
                        </div>
                    `,
                };
            }

            // -----------------------------------------------------------------
            // Chart 4: Footprint Summary Horizons (kg CO2e) — Grouped Bar
            // -----------------------------------------------------------------
            const c4 = document.getElementById("canvas-ind-summary");
            if (c4) {
                const dailyKg = indData.daily_co2e_kg || (indData.daily_co2e_g ? indData.daily_co2e_g / 1000.0 : 0);
                const monthlyKg = indData.monthly_co2e_kg || 0;
                const yearlyKg = indData.yearly_co2e_kg || 0;

                const horizonLabels = ["Daily Baseline", "Monthly (30d)", "Annualized (365d)"];
                const horizonValues = [dailyKg, monthlyKg, yearlyKg];

                const config4 = {
                    type: "bar",
                    data: {
                        labels: horizonLabels,
                        datasets: [
                            {
                                label: "Estimated CO₂e (kg)",
                                data: horizonValues,
                                backgroundColor: [THEME.mintSage, THEME.sageDeep, THEME.forest],
                                borderColor: THEME.forestDark,
                                borderWidth: 1,
                                borderRadius: 4,
                                hoverBackgroundColor: THEME.mint,
                            },
                        ],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: { duration: 750, easing: "easeOutQuart" },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: function (ctx) {
                                        return ` Projected Footprint: ${ctx.raw.toFixed(2)} kg CO₂e`;
                                    },
                                },
                            },
                        },
                        scales: {
                            y: {
                                grid: { color: THEME.grid },
                                title: { display: true, text: "Emissions (kg CO₂e)", font: { weight: "600" } },
                                beginAtZero: true,
                            },
                            x: {
                                grid: { display: false },
                                ticks: { font: { weight: "600" } },
                            },
                        },
                    },
                };

                const chart4 = new Chart(c4.getContext("2d"), config4);
                chartRegistry["ind-summary"] = {
                    title: "Footprint Summary across Time Horizons",
                    subtitle: "Comparison of single-day baseline against annualized cumulative emission projections.",
                    config: config4,
                    detailsHtml: `
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; text-align: center;">
                            <div style="background: #FFFFFF; border: 1px solid var(--border-color); border-radius: 4px; padding: 0.75rem;">
                                <div style="font-size: 0.75rem; color: var(--text-muted);">Daily Baseline</div>
                                <div style="font-size: 1.25rem; font-weight: 700; color: var(--color-forest);">${dailyKg.toFixed(3)} kg</div>
                            </div>
                            <div style="background: #FFFFFF; border: 1px solid var(--border-color); border-radius: 4px; padding: 0.75rem;">
                                <div style="font-size: 0.75rem; color: var(--text-muted);">Monthly (30 Days)</div>
                                <div style="font-size: 1.25rem; font-weight: 700; color: var(--color-forest);">${monthlyKg.toFixed(2)} kg</div>
                            </div>
                            <div style="background: #FFFFFF; border: 1px solid var(--border-color); border-radius: 4px; padding: 0.75rem;">
                                <div style="font-size: 0.75rem; color: var(--text-muted);">Annual (365 Days)</div>
                                <div style="font-size: 1.25rem; font-weight: 700; color: var(--color-forest);">${yearlyKg.toFixed(1)} kg</div>
                            </div>
                        </div>
                    `,
                };
            }
        } catch (err) {
            console.error("Error initializing individual dashboard interactive charts:", err);
        }
    }

    // =====================================================================
    // 9. Organization Dashboard Interactive Visualizations
    // =====================================================================
    const orgSummaryEl = document.getElementById("org-summary-data");
    if (orgSummaryEl) {
        try {
            const orgSummary = JSON.parse(orgSummaryEl.textContent);
            const activities = orgSummary.activities || {};
            const departments = orgSummary.departments || [];

            // -----------------------------------------------------------------
            // Chart 1: Organization Emissions by Activity (kg CO2e)
            // -----------------------------------------------------------------
            const cOrgAct = document.getElementById("canvas-org-act-co2");
            if (cOrgAct && Object.keys(activities).length > 0) {
                const actNames = Object.keys(activities);
                const actCo2 = actNames.map((k) => activities[k].co2e_kg || 0);
                const actPcts = actNames.map((k) => activities[k].percentage || 0);

                const configOrgAct = {
                    type: "bar",
                    data: {
                        labels: actNames.map((s) => s.charAt(0).toUpperCase() + s.slice(1)),
                        datasets: [
                            {
                                label: "Emissions (kg CO₂e)",
                                data: actCo2,
                                backgroundColor: PALETTE.slice(0, actNames.length),
                                borderColor: THEME.forest,
                                borderWidth: 1,
                                borderRadius: 4,
                                hoverBackgroundColor: THEME.mintSage,
                            },
                        ],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: { duration: 750, easing: "easeOutQuart" },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: function (ctx) {
                                        const idx = ctx.dataIndex;
                                        const val = ctx.raw;
                                        const pct = actPcts[idx] || 0;
                                        return ` ${val.toFixed(2)} kg CO₂e (${pct.toFixed(1)}% of total emissions)`;
                                    },
                                },
                            },
                        },
                        scales: {
                            y: {
                                grid: { color: THEME.grid },
                                title: { display: true, text: "Emissions (kg CO₂e)", font: { weight: "600" } },
                                beginAtZero: true,
                            },
                            x: {
                                grid: { display: false },
                                ticks: { font: { weight: "600" } },
                            },
                        },
                    },
                };

                const chartOrgAct = new Chart(cOrgAct.getContext("2d"), configOrgAct);
                chartRegistry["org-act-co2"] = {
                    title: "Organization Emissions by Activity Category",
                    subtitle: "Aggregated kilogram CO₂e emissions from telemetry records across organizational workload.",
                    config: configOrgAct,
                };
            }

            // -----------------------------------------------------------------
            // Chart 2: Organization Emissions by Department (kg CO2e)
            // -----------------------------------------------------------------
            const cOrgDept = document.getElementById("canvas-org-dept-co2");
            if (cOrgDept && departments.length > 0) {
                const deptNames = departments.map((d) => d.department || "Unknown");
                const deptCo2 = departments.map((d) => d.co2e_kg || 0);
                const deptHeadcount = departments.map((d) => d.records || 0);
                const deptMean = departments.map((d) => d.mean_co2e_kg || 0);

                const configOrgDept = {
                    type: "bar",
                    data: {
                        labels: deptNames,
                        datasets: [
                            {
                                label: "Department Total (kg CO₂e)",
                                data: deptCo2,
                                backgroundColor: THEME.sageDeep,
                                borderColor: THEME.forest,
                                borderWidth: 1,
                                borderRadius: 4,
                                hoverBackgroundColor: THEME.mintSage,
                            },
                        ],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: { duration: 750, easing: "easeOutQuart" },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: function (ctx) {
                                        const idx = ctx.dataIndex;
                                        const val = ctx.raw;
                                        const head = deptHeadcount[idx];
                                        const mean = deptMean[idx];
                                        return [
                                            ` Total: ${val.toFixed(2)} kg CO₂e`,
                                            ` Monitored: ${head} employees`,
                                            ` Mean per Employee: ${mean.toFixed(3)} kg`,
                                        ];
                                    },
                                },
                            },
                        },
                        scales: {
                            y: {
                                grid: { color: THEME.grid },
                                title: { display: true, text: "Emissions (kg CO₂e)", font: { weight: "600" } },
                                beginAtZero: true,
                            },
                            x: {
                                grid: { display: false },
                                ticks: { font: { weight: "600" } },
                            },
                        },
                    },
                };

                const chartOrgDept = new Chart(cOrgDept.getContext("2d"), configOrgDept);
                chartRegistry["org-dept-co2"] = {
                    title: "Departmental Carbon Footprint Ranking",
                    subtitle: "Division emissions aggregated from telemetry records with per-employee intensity metrics.",
                    config: configOrgDept,
                };
            }
        } catch (err) {
            console.error("Error initializing organization dashboard interactive charts:", err);
        }
    }

    // =====================================================================
    // 10. Organization Departments Page Interactive Chart
    // =====================================================================
    const deptsListEl = document.getElementById("departments-list-data");
    if (deptsListEl) {
        try {
            const depts = JSON.parse(deptsListEl.textContent);
            const cDeptsPage = document.getElementById("canvas-depts-page-co2");

            if (cDeptsPage && Array.isArray(depts) && depts.length > 0) {
                const names = depts.map((d) => d.department);
                const totals = depts.map((d) => d.co2e_kg || 0);
                const energies = depts.map((d) => d.energy_kwh || 0);
                const means = depts.map((d) => d.mean_co2e_kg || 0);
                const counts = depts.map((d) => d.records || 0);

                const configDeptsPage = {
                    type: "bar",
                    data: {
                        labels: names,
                        datasets: [
                            {
                                label: "Daily Total Emissions (kg CO₂e)",
                                data: totals,
                                backgroundColor: THEME.forest,
                                borderColor: THEME.forestDark,
                                borderWidth: 1,
                                borderRadius: 4,
                                yAxisID: "y",
                            },
                            {
                                label: "Mean per Employee (kg CO₂e)",
                                data: means,
                                backgroundColor: THEME.mintSage,
                                borderColor: THEME.sageDeep,
                                borderWidth: 1,
                                borderRadius: 4,
                                yAxisID: "y1",
                            },
                        ],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: { duration: 750, easing: "easeOutQuart" },
                        plugins: {
                            legend: {
                                position: "top",
                                labels: { font: { weight: "600" }, padding: 12 },
                            },
                            tooltip: {
                                callbacks: {
                                    afterBody: function (items) {
                                        if (items.length > 0) {
                                            const idx = items[0].dataIndex;
                                            return `Headcount: ${counts[idx]} | Direct Energy: ${energies[idx].toFixed(3)} kWh`;
                                        }
                                        return "";
                                    },
                                },
                            },
                        },
                        scales: {
                            y: {
                                type: "linear",
                                display: true,
                                position: "left",
                                title: { display: true, text: "Total Department CO₂e (kg)", font: { weight: "600" } },
                                grid: { color: THEME.grid },
                                beginAtZero: true,
                            },
                            y1: {
                                type: "linear",
                                display: true,
                                position: "right",
                                title: { display: true, text: "Mean per Employee (kg)", font: { weight: "600" } },
                                grid: { drawOnChartArea: false },
                                beginAtZero: true,
                            },
                            x: {
                                grid: { display: false },
                                ticks: { font: { weight: "600" } },
                            },
                        },
                    },
                };

                const chartDeptsPage = new Chart(cDeptsPage.getContext("2d"), configDeptsPage);
                chartRegistry["depts-page-co2"] = {
                    title: "Departmental Comparative Emissions & Intensity",
                    subtitle: "Dual-axis comparison of gross carbon emissions against per-capita intensity by department.",
                    config: configDeptsPage,
                };
            }
        } catch (err) {
            console.error("Error initializing departments page interactive chart:", err);
        }
    }
});
