// Assumes auth and axios are loaded globally via CDN
// If you use QR scanning, ensure jsQR is loaded via CDN in your HTML as well

document.addEventListener("DOMContentLoaded", function() {
  // Check authentication and initialize
  if (!auth.requireAuth() || !auth.hasRole("student")) {
    window.location.href = "/login";
    return;
  }

  // Initialize dashboard and load data
  initializeDashboard()
    .then(() => {
      // Set up QR scanner
      setupQRScanner();

      // Set up camera attendance
      setupCameraAttendance();

      // Load dashboard data
      loadDashboardData();

      // Set current date
      document.getElementById("current-date").textContent = new Date().toLocaleDateString();
    })
    .catch(error => {
      console.error("Error initializing dashboard:", error);
      showError("Failed to initialize dashboard");
    });
// --- Camera Attendance Modal Logic ---
function setupCameraAttendance() {
  const fallbackBtn = document.getElementById("fallback-qr-btn");
  if (fallbackBtn) {
    fallbackBtn.addEventListener("click", () => {
      document.getElementById("camera-attendance-modal").classList.add("hidden");
      // Show QR scanner section
      document.getElementById("qr-scanner").classList.remove("hidden");
      document.getElementById("scan-qr-btn").classList.add("hidden");
    });
  }
  const cameraBtn = document.getElementById("camera-attendance-btn");
  const cameraModal = document.getElementById("camera-attendance-modal");
  const closeCameraModal = document.getElementById("close-camera-modal");
  const video = document.getElementById("camera-attendance-video");
  const scanBtn = document.getElementById("scan-face-btn");
  const feedback = document.getElementById("camera-attendance-feedback");
  let stream = null;

  if (cameraBtn) {
    cameraBtn.addEventListener("click", async () => {
      cameraModal.classList.remove("hidden");
      // Load all today's sessions for dropdown (for facial attendance)
      try {
        const res = await axios.get("/api/attendance/sessions/today/all");
        const select = document.getElementById("session-select");
        select.innerHTML = "";
        if ((res.data.sessions || []).length === 0) {
          const option = document.createElement("option");
          option.value = "";
          option.textContent = "No sessions available";
          select.appendChild(option);
        } else {
          let now = new Date();
          let selectedSessionId = null;
          (res.data.sessions || []).forEach(s => {
            const startDate = new Date(s.start_time);
            const endDate = s.end_time ? new Date(s.end_time) : null;
            const start = startDate.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
            const end = endDate ? endDate.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }) : "--:--";
            const option = document.createElement("option");
            option.value = s.id;
            option.textContent = `${s.subject} (${start} - ${end})`;
            // Auto-select if now is between start and end
            if (startDate <= now && (!endDate || now <= endDate)) {
              selectedSessionId = s.id;
            }
            select.appendChild(option);
          });
          if (selectedSessionId) {
            select.value = selectedSessionId;
          }
        }
      } catch (err) {
        feedback.textContent = "Could not fetch sessions.";
      }
      // Start webcam reliably
      try {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
          stream = await navigator.mediaDevices.getUserMedia({ video: true });
          video.srcObject = stream;
          await video.play();
        } else {
          feedback.textContent = "Camera not supported on this device.";
        }
      } catch (err) {
        feedback.textContent = "Unable to access camera. Please check permissions or use a supported device.";
      }
    });
  }
  if (closeCameraModal) {
    closeCameraModal.addEventListener("click", () => {
      cameraModal.classList.add("hidden");
      feedback.textContent = "";
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
      }
    });
  }
  if (scanBtn) {
    scanBtn.addEventListener("click", async () => {
      feedback.textContent = "Scanning...";
      // Get selected session from dropdown
      const select = document.getElementById("session-select");
      const sessionId = select.value;
      if (!sessionId) {
        feedback.textContent = "Please select a session.";
        return;
      }
      // Capture frame
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext("2d").drawImage(video, 0, 0);
      const dataUrl = canvas.toDataURL("image/jpeg");
      // Send to backend for recognition
      try {
        const res = await axios.post("/api/ai/recognize_face", {
          image: dataUrl,
          session_id: sessionId
        });
        if (res.data.match) {
          if (res.data.attendance === "marked") {
            feedback.textContent = `✅ ${res.data.name} – Attendance Marked`;
          } else {
            feedback.textContent = `Already marked for ${res.data.name}`;
          }
          // Optionally refresh dashboard
          setTimeout(() => {
            loadDashboardData();
            cameraModal.classList.add("hidden");
            if (stream) {
              stream.getTracks().forEach(track => track.stop());
              stream = null;
            }
          }, 2000);
        } else {
          feedback.textContent = "Unknown face. Try again.";
        }
      } catch (err) {
        feedback.textContent = err.response?.data?.error || "Recognition failed.";
      }
    });
  }
}
});

async function initializeDashboard() {
  const user = auth.user;
  if (user) {
    // Update welcome message with proper name formatting
    const welcomeMessage = document.getElementById("welcome-message");
    welcomeMessage.textContent = `Welcome back, ${user.name || 'Student'}!`;

    // Update student info with complete details
    const studentInfo = document.getElementById("student-info");
    let infoText = '';
    
    if (user.standard && user.division) {
      infoText += `Class ${user.standard}-${user.division}`;
    }
    
    if (user.roll_no) {
      infoText += infoText ? ` • Roll No: ${user.roll_no}` : `Roll No: ${user.roll_no}`;
    }
    
    if (!infoText) {
      infoText = 'Loading student information...';
    }
    
    studentInfo.textContent = infoText;

    // Try to fetch additional student details if needed
    try {
      const response = await axios.get('/api/student/dashboard');
      if (response.data) {
        welcomeMessage.textContent = `Welcome back, ${user.name}!`;
        // Update statistics
        if (response.data.stats) {
          const stats = response.data.stats;
          document.getElementById("present-count").textContent = 
            `${stats.present_today}/${stats.total_today}`;
          document.getElementById("week-attendance").textContent = 
            stats.weekly_total > 0 
              ? `${Math.round((stats.weekly_present / stats.weekly_total) * 100)}%`
              : '0%';
          document.getElementById("pending-tasks").textContent = 
            stats.pending_tasks || '0';
          document.getElementById("overall-percentage").textContent = 
            stats.weekly_total > 0
              ? `${Math.round((stats.weekly_present / stats.weekly_total) * 100)}%`
              : '0%';
        }
      }
    } catch (error) {
      console.error('Error fetching additional student data:', error);
    }
  }
}

async function loadDashboardData() {
  try {
    // Load today's sessions
    const sessionsResponse = await axios.get("/api/attendance/sessions/today");
    displayTodaySchedule(sessionsResponse.data.sessions);

    // Update stats
    updateAttendanceStats(sessionsResponse.data.sessions);

    // Load recent activity
    loadRecentActivity();
  } catch (error) {
    console.error("Error loading dashboard data:", error);
    showError("Failed to load dashboard data");
  }
}

function displayTodaySchedule(sessions) {
  const scheduleContainer = document.getElementById("today-schedule");

  if (!sessions || sessions.length === 0) {
    scheduleContainer.innerHTML = `
      <div class="text-center py-8 text-gray-500">
        <i class="fas fa-calendar-times text-3xl mb-3"></i>
        <p>No classes scheduled for today</p>
      </div>
    `;
    return;
  }

  scheduleContainer.innerHTML = sessions
    .map((session) => {
      const startTime = new Date(session.start_time).toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      });

      const endTime = session.end_time ? new Date(session.end_time).toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      }) : null;

      const timeDisplay = endTime ? `${startTime} - ${endTime}` : startTime;

      const statusClass =
        session.attendance_status === "present"
          ? "bg-green-100 text-green-800"
          : session.attendance_status === "late"
            ? "bg-yellow-100 text-yellow-800"
            : "bg-red-100 text-red-800";

      const statusIcon =
        session.attendance_status === "present"
          ? "fa-check-circle"
          : session.attendance_status === "late"
            ? "fa-clock"
            : "fa-times-circle";

      // Format marked time if available
      const markedTime = session.marked_at 
        ? new Date(session.marked_at).toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
          })
        : null;

      // Add additional details about who marked the attendance
      const markedDetails = markedTime 
        ? `<div class="text-xs text-gray-500 mt-1">
             <i class="fas fa-clock mr-1"></i> Marked at ${markedTime}
             ${session.marked_by ? `<span class="mx-1">•</span> ${session.marked_by === 'face' ? 'Face Recognition' : session.marked_by}` : ''}
           </div>`
        : '';

      return `
        <div class="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
          <div class="flex items-center">
            <div class="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mr-4">
              <i class="fas fa-book text-indigo-600"></i>
            </div>
            <div>
              <h4 class="font-semibold text-gray-900">${session.subject}</h4>
              <p class="text-sm text-gray-600">
                <i class="fas fa-user-tie mr-1"></i> ${session.teacher}
              </p>
              <p class="text-xs text-gray-500">
                <i class="far fa-clock mr-1"></i> ${timeDisplay}
              </p>
            </div>
          </div>
          <div class="text-right">
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusClass}">
              <i class="fas ${statusIcon} mr-1"></i>
              ${session.attendance_status || "Absent"}
            </span>
            ${markedDetails}
          </div>
        </div>
      `;
    })
    .join("");
}

function updateAttendanceStats(sessions) {
  const presentToday = sessions.filter((s) => s.attendance_status === "present").length;
  const totalToday = sessions.length;

  document.getElementById("present-count").textContent = `${presentToday}/${totalToday}`;

  // Calculate percentage
  const percentage = totalToday > 0 ? Math.round((presentToday / totalToday) * 100) : 0;
  document.getElementById("overall-percentage").textContent = `${percentage}%`;

  // Placeholder values for week attendance and pending tasks
  document.getElementById("week-attendance").textContent = "85%";
  document.getElementById("pending-tasks").textContent = "3";
}

function setupQRScanner() {
  const fallbackManualBtn = document.getElementById("fallback-manual-btn");
  if (fallbackManualBtn) {
    fallbackManualBtn.addEventListener("click", () => {
      document.getElementById("qr-scanner").classList.add("hidden");
      document.getElementById("manual-entry").scrollIntoView({ behavior: "smooth" });
      document.getElementById("manual-qr-input").focus();
    });
  }
  const scanBtn = document.getElementById("scan-qr-btn");
  const stopBtn = document.getElementById("stop-scan-btn");
  const scanner = document.getElementById("qr-scanner");
  const video = document.getElementById("qr-video");
  const manualSubmit = document.getElementById("submit-manual-qr");

  let stream = null;
  let scanning = false;

  scanBtn.addEventListener("click", startQRScanner);
  stopBtn.addEventListener("click", stopQRScanner);
  manualSubmit.addEventListener("click", submitManualQR);
  // Hide camera when switching modes
  document.getElementById("camera-attendance-modal").addEventListener("transitionend", () => {
    if (document.getElementById("camera-attendance-modal").classList.contains("hidden")) {
      const video = document.getElementById("camera-attendance-video");
      if (video && video.srcObject) {
        video.srcObject.getTracks().forEach(track => track.stop());
        video.srcObject = null;
      }
    }
  });

  async function startQRScanner() {
    try {
      // Check if MediaDevices API is available
      // Show manual input if camera is not supported
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showError('Camera not supported on this device. Please use manual code entry below.');
        document.getElementById("manual-entry").classList.add("mt-4", "border-t", "pt-4");
        document.getElementById("manual-qr-input").focus();
        return;
      }

      try {
        // Request camera access
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment" },
        });
        video.srcObject = stream;
        scanner.classList.remove("hidden");
        scanBtn.classList.add("hidden");
        scanning = true;

        // Start scanning for QR codes
        scanForQRCode();
      } catch (error) {
        console.error("Camera access error:", error);
        showError('Camera access failed. Please use manual code entry below.');
        document.getElementById("manual-entry").classList.add("mt-4", "border-t", "pt-4");
        document.getElementById("manual-qr-input").focus();
      }
    } catch (error) {
      console.error("Error accessing camera:", error);
      let errorMessage = "Unable to access camera. ";
      
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        errorMessage += "Please grant camera permission in your browser settings.";
      } else if (error.name === 'NotFoundError') {
        errorMessage += "No camera found on your device.";
      } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
        errorMessage += "Camera is already in use by another application.";
      } else if (error.name === 'SecurityError') {
        errorMessage += "Camera access is restricted (try using HTTPS or localhost).";
      } else {
        errorMessage += error.message || "Please check your camera permissions.";
      }
      
      showError(errorMessage);
    }
  }

  function stopQRScanner() {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
    scanner.classList.add("hidden");
    scanBtn.classList.remove("hidden");
    scanning = false;
  }

  function scanForQRCode() {
    if (!scanning) return;

    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");

    if (video.readyState === video.HAVE_ENOUGH_DATA) {
      canvas.height = video.videoHeight;
      canvas.width = video.videoWidth;
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
      const code = jsQR(imageData.data, imageData.width, imageData.height);

      if (code) {
        processQRCode(code.data);
        stopQRScanner();
        return;
      }
    }

    requestAnimationFrame(scanForQRCode);
  }

  async function submitManualQR() {
    const qrInput = document.getElementById("manual-qr-input");
    const qrCode = qrInput.value.trim();

    if (!qrCode) {
      showError("Please enter a QR code");
      return;
    }

    await processQRCode(qrCode);
    qrInput.value = "";
  }

  async function processQRCode(qrData) {
    try {
      let payload = {};
      
      // Check if input is a short manual code (6 characters) or QR token
      if (qrData.length <= 6) {
        payload = { manual_code: qrData.toUpperCase() };
      } else {
        // Handle QR token
        let qrToken = qrData;
        
        // Check if the data is in the format "attendance:token:timetable_id"
        if (qrData.includes(":")) {
          const parts = qrData.split(":");
          if (parts.length === 3 && parts[0] === "attendance") {
            qrToken = parts[1];
          }
        }
        
        payload = { qr_token: qrToken };
      }

      // Submit attendance
      const response = await axios.post("/api/attendance/mark-qr", payload);

      showSuccess("Attendance marked successfully!");

      // Refresh dashboard data
      setTimeout(() => {
        loadDashboardData();
      }, 1000);
    } catch (error) {
      console.error("Error marking attendance:", error);
      const errorMessage = error.response?.data?.error || "Failed to mark attendance";
      showError(errorMessage);
    }
  }
}

async function loadRecentActivity() {
  // Placeholder for recent activity
  const activityContainer = document.getElementById("recent-activity");

  const activities = [
    { icon: "fa-check-circle", text: "Marked present for Mathematics", time: "2 hours ago", color: "text-green-600" },
    { icon: "fa-tasks", text: "Completed Physics assignment", time: "1 day ago", color: "text-blue-600" },
    { icon: "fa-clock", text: "Late arrival for Chemistry", time: "2 days ago", color: "text-yellow-600" },
  ];

  activityContainer.innerHTML = activities
    .map(activity => `
      <div class="flex items-center p-3 rounded-lg hover:bg-gray-50 transition-colors">
        <i class="fas ${activity.icon} ${activity.color} mr-3"></i>
        <div class="flex-1">
          <p class="text-sm text-gray-900">${activity.text}</p>
          <p class="text-xs text-gray-500">${activity.time}</p>
        </div>
      </div>
    `)
    .join("");
}

function showSuccess(message) {
  const successDiv = document.getElementById("attendance-success");
  successDiv.querySelector("span").textContent = message;
  successDiv.classList.remove("hidden");

  setTimeout(() => {
    successDiv.classList.add("hidden");
  }, 5000);
}

function showError(message) {
  const errorDiv = document.getElementById("attendance-error");
  document.getElementById("error-text").textContent = message;
  errorDiv.classList.remove("hidden");

  setTimeout(() => {
    errorDiv.classList.add("hidden");
  }, 5000);
}
