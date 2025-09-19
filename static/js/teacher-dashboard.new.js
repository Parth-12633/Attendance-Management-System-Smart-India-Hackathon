// Import necessary modules
document.addEventListener("DOMContentLoaded", async () => {
  // Check authentication
  if (!auth.requireAuth() || !auth.hasRole("teacher")) {
    return;
  }

  // Initialize dashboard
  await initializeDashboard();
  setupEventListeners();
  loadDashboardData();

  // Set current date
  document.getElementById("current-date").textContent = new Date().toLocaleDateString();

  // Auto-refresh attendance every 30 seconds
  setInterval(refreshAttendance, 30000);
});

let currentQRSession = null;
let qrExpiryTimer = null;

async function initializeDashboard() {
  const user = auth.user;
  if (user) {
    document.getElementById("welcome-message").textContent = `Welcome back, ${user.name}!`;
    document.getElementById("teacher-info").textContent =
      `${user.department || "Teacher"} • Employee ID: ${user.employee_id || "N/A"}`;
  }
}

function setupEventListeners() {
  // QR Code Generation
  document.getElementById("generate-qr-btn").addEventListener("click", showQRGenerator);
  document.getElementById("session-select").addEventListener("change", toggleGenerateButton);
  document.getElementById("generate-session-qr").addEventListener("click", generateQRCode);
  document.getElementById("download-qr").addEventListener("click", downloadQRCode);

  // Create Session Modal
  document.getElementById("open-create-session").addEventListener("click", () => {
    document.getElementById("create-session-modal").classList.remove("hidden");
  });
  document.getElementById("close-create-session").addEventListener("click", () => {
    document.getElementById("create-session-modal").classList.add("hidden");
  });
  document.getElementById("create-session-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    await submitCreateSessionForm();
  });

  // Manual Attendance
  document.getElementById("manual-attendance-btn").addEventListener("click", openManualAttendance);
  document.getElementById("close-manual-modal").addEventListener("click", closeManualAttendance);
  document.getElementById("cancel-manual").addEventListener("click", closeManualAttendance);
  document.getElementById("save-manual-attendance").addEventListener("click", saveManualAttendance);
  document.getElementById("manual-session-select").addEventListener("change", loadStudentList);

  // Other actions
  document.getElementById("refresh-attendance").addEventListener("click", refreshAttendance);
  document.getElementById("attendance-report-btn").addEventListener("click", generateReport);
  document.getElementById("class-filter").addEventListener("change", filterAttendance);
}

async function generateQRCode() {
  const sessionSelect = document.getElementById("session-select");
  const sessionId = sessionSelect.value;
  const subjectSelect = document.getElementById('subject-select');
  const subject = subjectSelect ? subjectSelect.value : null;

  if (!sessionId) {
    showError("Please select a session");
    return;
  }

  try {
    // Call teacher QR generation endpoint (include subject)
    const response = await axios.post(`/api/teacher/session/${sessionId}/generate_qr`, { subject });

    const { qr_code, jwt, expires_in } = response.data;

    // Display QR code (qr_code is a data URL from the API)
    const qrDisplay = document.getElementById("qr-display");
    const qrPlaceholder = document.getElementById("qr-placeholder");
    const qrInfo = document.getElementById("qr-info");
    const manualCode = document.getElementById("manual-code");

    qrPlaceholder.innerHTML = `<img src="${qr_code}" alt="QR Code" class="w-48 h-48 mx-auto">`;
    qrInfo.classList.remove("hidden");

    // Display and setup manual code
    manualCode.textContent = jwt;
    setupCopyCodeButton(jwt);

    // Store current session info
    currentQRSession = {
      qr_code,
      jwt,
      expires_at: new Date(Date.now() + expires_in * 1000),
    };

    // Start expiry countdown
    startQRExpiryCountdown(expires_in);
    
    showSuccess("QR Code generated successfully!");
  } catch (error) {
    console.error("Error generating QR code:", error);
    showError(error.response?.data?.error || "Failed to generate QR code");
  }
}

function setupCopyCodeButton(code) {
  const copyBtn = document.getElementById("copy-code");
  
  copyBtn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(code);
      
      // Visual feedback
      copyBtn.innerHTML = '<i class="fas fa-check"></i>';
      copyBtn.classList.add("text-green-600");
      
      setTimeout(() => {
        copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
        copyBtn.classList.remove("text-green-600");
      }, 2000);
      
      showSuccess("Code copied to clipboard!");
    } catch (err) {
      showError("Failed to copy code. Please try selecting and copying manually.");
    }
  });
}

function startQRExpiryCountdown(expiresIn) {
  const qrExpires = document.getElementById("qr-expires");

  if (qrExpiryTimer) {
    clearInterval(qrExpiryTimer);
  }

  let timeLeft = expiresIn;

  qrExpiryTimer = setInterval(() => {
    timeLeft--;

    if (timeLeft <= 0) {
      clearInterval(qrExpiryTimer);
      qrExpires.textContent = "Expired";
      document.getElementById("qr-info").classList.add("hidden");
      document.getElementById("qr-placeholder").innerHTML = `
        <div class="text-gray-400">
          <i class="fas fa-qrcode text-4xl mb-2"></i>
          <p class="text-sm">QR Code will appear here</p>
        </div>
      `;
      return;
    }

    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    qrExpires.textContent = `Expires in: ${minutes}:${seconds.toString().padStart(2, "0")}`;
  }, 1000);
}

// ... Rest of the file remains the same ...