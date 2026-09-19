/**
 * CarbonLens — Client-Side Progressive Enhancements
 * Provides drag-and-drop file interactions and dynamic slider readouts.
 */

document.addEventListener("DOMContentLoaded", function () {
    // ---------------------------------------------------------------------
    // Drag and Drop Upload Handler
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
    // What-If Simulation Sliders
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
    // Tab switching for Registration Page
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
});
