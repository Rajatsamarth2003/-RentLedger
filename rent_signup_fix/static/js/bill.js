const imageInput = document.getElementById("meterImage");
const fileName = document.getElementById("fileName");
const scanBtn = document.getElementById("scanBtn");
const scanStatus = document.getElementById("scanStatus");
const billingMonth = document.getElementById("billingMonth");
const billForm = document.getElementById("billForm");
const familyId = billForm?.dataset.familyId;
const previousReadingInput = document.getElementById("previousReading");
const previousBadge = document.getElementById("previousBadge");
const previousSource = document.getElementById("previousSource");

const ocrResult = document.getElementById("ocrResult");
const ocrReading = document.getElementById("ocrReading");
const ocrConfidence = document.getElementById("ocrConfidence");
const ocrMessage = document.getElementById("ocrMessage");

const ocrReadingInput = document.getElementById("ocrReadingInput");
const ocrConfidenceInput = document.getElementById("ocrConfidenceInput");

const currentReading = document.getElementById("currentReading");
const enteredUnits = document.getElementById("enteredUnits");
const rentInput = document.querySelector('input[name="rent"]');
const matchBox = document.getElementById("matchBox");

const previewRent = document.getElementById("previewRent");
const previewUnits = document.getElementById("previewUnits");
const previewRate = document.getElementById("previewRate");
const previewElectricity = document.getElementById("previewElectricity");
const previewTotal = document.getElementById("previewTotal");

let previousReading = Number(previousReadingInput?.value || 0);

function setPreviousReading(value, sourceMonth) {
    previousReading = Number(value || 0);

    if (previousReadingInput) {
        previousReadingInput.value = previousReading;
    }

    if (previousBadge) {
        previousBadge.textContent = `Previous: ${Math.round(previousReading)}`;
    }

    if (previousSource) {
        if (sourceMonth) {
            previousSource.textContent = `Automatically taken from the last saved bill (${sourceMonth}).`;
        } else {
            previousSource.textContent = "No earlier bill found for this family. Starting from 0.";
        }
    }

    updateMatch();
}

async function loadPreviousReading() {
    const month = billingMonth?.value;
    if (!month) return;

    try {
        const response = await fetch(`/families/${familyId}/previous-reading?month=${encodeURIComponent(month)}`);
        const result = await response.json();

        if (result.success) {
            setPreviousReading(result.previous_reading, result.source_month);
        }
    } catch (error) {
        // Keep the server-provided value if the lookup cannot be refreshed.
    }
}

billingMonth?.addEventListener("change", loadPreviousReading);

imageInput?.addEventListener("change", () => {
    if (imageInput.files.length) {
        fileName.textContent = imageInput.files[0].name;
    }
});

scanBtn?.addEventListener("click", async () => {
    if (!imageInput.files.length) {
        alert("Please choose a meter photo first.");
        return;
    }

    scanBtn.disabled = true;
    scanBtn.textContent = "Scanning…";
    scanStatus.textContent = "Reading the photo…";

    const data = new FormData();
    data.append("meter_image", imageInput.files[0]);

    try {
        const response = await fetch("/ocr", {
            method: "POST",
            body: data
        });

        const result = await response.json();

        ocrResult.classList.remove("hidden");

        if (result.success) {
            ocrReading.textContent = Math.round(result.reading);
            ocrConfidence.textContent = result.confidence
                ? `${(result.confidence * 100).toFixed(1)}%`
                : "N/A";

            ocrReadingInput.value = result.reading;
            ocrConfidenceInput.value = result.confidence || "";

            // OCR only proposes the current month's reading. It never changes
            // the automatic previous reading.
            currentReading.value = result.reading;
            ocrMessage.textContent = "Current reading filled in for you. Please verify it against the photo.";
            scanStatus.textContent = "Scan complete — please verify.";
            updatePreview();
            updateMatch();
        } else {
            ocrReading.textContent = "Not found";
            ocrConfidence.textContent = "—";
            ocrMessage.textContent = result.message || "Try a clearer photo with the digits facing the camera.";
            scanStatus.textContent = "Could not detect a number.";
        }
    } catch (error) {
        ocrResult.classList.remove("hidden");
        ocrReading.textContent = "Error";
        ocrConfidence.textContent = "—";
        ocrMessage.textContent = "OCR could not run. You can still enter the reading manually.";
        scanStatus.textContent = "Manual entry available.";
    } finally {
        scanBtn.disabled = false;
        scanBtn.textContent = "Scan photo";
    }
});

function selectedRate() {
    return Number(document.querySelector('input[name="rate"]:checked')?.value || 0);
}

function updatePreview() {
    const rent = Number(rentInput?.value || 0);
    const units = Number(enteredUnits?.value || 0);
    const rate = selectedRate();

    const electricity = units * rate;
    const total = rent + electricity;

    previewRent.textContent = `₹${rent.toLocaleString("en-IN", {maximumFractionDigits: 0})}`;
    previewUnits.textContent = units ? units.toLocaleString("en-IN") : "—";
    previewRate.textContent = rate ? `₹${rate}/unit` : "—";
    previewElectricity.textContent = `₹${electricity.toLocaleString("en-IN", {maximumFractionDigits: 0})}`;
    previewTotal.textContent = `₹${total.toLocaleString("en-IN", {maximumFractionDigits: 0})}`;
}

function updateMatch() {
    const current = Number(currentReading?.value || 0);
    const units = Number(enteredUnits?.value || 0);

    if (!currentReading?.value || !enteredUnits?.value) {
        matchBox.className = "match-box hidden";
        return;
    }

    const calculated = current - previousReading;
    const difference = Math.abs(units - calculated);

    matchBox.classList.remove("hidden");

    if (calculated < 0) {
        matchBox.className = "match-box match-warn";
        matchBox.textContent = `⚠ Current reading is below the previous reading (${previousReading.toFixed(0)}). Check the meter reading.`;
        return;
    }

    if (difference < 0.01) {
        matchBox.className = "match-box match-good";
        matchBox.textContent = `✓ Cross-check matched: ${calculated.toFixed(0)} units`;
    } else {
        matchBox.className = "match-box match-warn";
        matchBox.textContent = `⚠ Meter difference: ${calculated.toFixed(0)} units vs your ${units.toFixed(0)} units`;
    }
}

[rentInput, currentReading, enteredUnits].forEach((el) => {
    el?.addEventListener("input", () => {
        updatePreview();
        updateMatch();
    });
});

document.querySelectorAll('input[name="rate"]').forEach((el) => {
    el.addEventListener("change", updatePreview);
});

updatePreview();
loadPreviousReading();
