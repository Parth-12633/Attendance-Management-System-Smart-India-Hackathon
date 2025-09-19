// Import necessary modules
// const auth = require("./auth") // Removed for browser global
// const axios = require("axios") // axios is loaded globally

document.addEventListener("DOMContentLoaded", async () => {
  // Check authentication
  if (!auth.requireAuth() || !auth.hasRole("teacher")) {
    return
  }

  // Initialize dashboard
  await initializeDashboard()
  setupEventListeners()
  loadDashboardData()

  // Set current date
  document.getElementById("current-date").textContent = new Date().toLocaleDateString()

  // Auto-refresh attendance every 10 seconds for near real-time updates
  setInterval(refreshAttendance, 10000)
})

let currentQRSession = null
let qrExpiryTimer = null

async function initializeDashboard() {
  const user = auth.user
  if (user) {
    document.getElementById("welcome-message").textContent = `Welcome back, ${user.name}!`
    document.getElementById("teacher-info").textContent =
      `${user.department || "Teacher"} • Employee ID: ${user.employee_id || "N/A"}`
  }
}

function setupEventListeners() {
  // QR Code Generation
  const addListener = (id, event, handler) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener(event, handler);
  };

  addListener("generate-qr-btn", "click", showQRGenerator);
  addListener("session-select", "change", toggleGenerateButton);
  addListener("generate-session-qr", "click", generateQRCode);
  addListener("download-qr", "click", downloadQRCode);

  // Create Session Modal
  addListener("open-create-session", "click", () => {
    document.getElementById("create-session-modal").classList.remove("hidden");
  });
  addListener("close-create-session", "click", () => {
    document.getElementById("create-session-modal").classList.add("hidden");
  });
  addListener("create-session-form", "submit", async (e) => {
    e.preventDefault();
    await submitCreateSessionForm();
  });

  // Manual Attendance
  addListener("manual-attendance-btn", "click", openManualAttendance);
  addListener("close-manual-modal", "click", closeManualAttendance);
  addListener("cancel-manual", "click", closeManualAttendance);
  addListener("save-manual-attendance", "click", saveManualAttendance);
  addListener("manual-session-select", "change", loadStudentList);

  // Camera Attendance
  // Camera attendance is now student-only; remove event listeners for teacher dashboard

  // Other actions
  addListener("refresh-attendance", "click", refreshAttendance);
  addListener("attendance-report-btn", "click", generateReport);
  addListener("class-filter", "change", filterAttendance);
}

async function submitCreateSessionForm() {
  const standard = document.getElementById("create-class-standard").value.trim();
  const division = document.getElementById("create-class-division").value.trim();
  const subjectName = document.getElementById("create-subject-name").value.trim();
  const subjectCode = document.getElementById("create-subject-code").value.trim();
  const room = document.getElementById("create-room-number").value.trim();
  const startTime = document.getElementById("create-session-start").value;
  const endTime = document.getElementById("create-session-end").value;

  if (!standard || !division || !subjectName || !subjectCode || !startTime || !endTime) {
    showError("Please fill in all required fields.");
    return;
  }

  try {
    const response = await axios.post("/api/teacher/create_session", {
      class_standard: standard,
      class_division: division,
      subject_name: subjectName,
      subject_code: subjectCode,
      room: room,
      start_time: startTime,
      end_time: endTime
    });
    showSuccess("Session created successfully!");
    document.getElementById("create-session-modal").classList.add("hidden");
    await loadDashboardData();
  } catch (error) {
    console.error("Error creating session:", error);
    showError(error.response?.data?.error || "Failed to create session");
  }
}

async function loadDashboardData() {
  try {
    // Load teacher's sessions for today
    const sessionsResponse = await axios.get("/api/teacher/sessions/today")
    const sessions = sessionsResponse.data.sessions

    // Populate session selects
    populateSessionSelects(sessions)

    // Display today's schedule
    displayTeacherSchedule(sessions)

    // Load attendance data
    await refreshAttendance()

    // Update stats
    updateTeacherStats(sessions)

    // Load recent activity
    loadRecentActivity()

    // Load attendance alerts
    loadAttendanceAlerts()
  } catch (error) {
    console.error("Error loading dashboard data:", error)
    showError("Failed to load dashboard data")
  }
}

function populateSessionSelects(sessions) {
  const sessionSelect = document.getElementById("session-select")
  const manualSessionSelect = document.getElementById("manual-session-select")

  // Clear existing options
  sessionSelect.innerHTML = '<option value="">Select a session...</option>'
  manualSessionSelect.innerHTML = '<option value="">Select a session...</option>'

  // Show all sessions for today so newly created sessions are visible
  sessions.forEach((session) => {
    const startTime = new Date(session.start_time).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });
    const endTime = session.end_time ? new Date(session.end_time).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    }) : "--:--";
    const status = session.is_active ? "Active" : "Scheduled";
    const option = `<option value="${session.id}">${session.subject} - ${session.class_name} (${startTime} - ${endTime}) [${status}]</option>`;
    sessionSelect.innerHTML += option;
    manualSessionSelect.innerHTML += option;
  });
}

function displayTeacherSchedule(sessions) {
  const scheduleContainer = document.getElementById("teacher-schedule")

  if (!sessions || sessions.length === 0) {
    scheduleContainer.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <i class="fas fa-calendar-times text-3xl mb-3"></i>
                <p>No classes scheduled for today</p>
            </div>
        `
    return
  }

  scheduleContainer.innerHTML = sessions
    .map((session) => {
      const startTime = new Date(session.start_time).toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      })
      const endTime = new Date(session.end_time).toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      })

      const statusClass = session.is_active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"

      return `
            <div class="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                <div class="flex items-center">
                    <div class="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mr-4">
                        <i class="fas fa-chalkboard-teacher text-indigo-600"></i>
                    </div>
                    <div>
                        <h4 class="font-semibold text-gray-900">${session.subject}</h4>
                        <p class="text-sm text-gray-600">${session.class_name} • ${session.room_number || "Room TBA"}</p>
                        <p class="text-sm text-gray-500">${startTime} - ${endTime}</p>
                    </div>
                </div>
                <div class="text-right">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusClass}">
                        ${session.is_active ? "Active" : "Scheduled"}
                    </span>
                    <p class="text-sm text-gray-500 mt-1">${session.attendance_count || 0} students marked</p>
                </div>
            </div>
        `
    })
    .join("")
}

function toggleGenerateButton() {
  const sessionSelect = document.getElementById("session-select")
  const generateBtn = document.getElementById("generate-session-qr")

  generateBtn.disabled = !sessionSelect.value
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
  const qrExpires = document.getElementById("qr-expires")

  if (qrExpiryTimer) {
    clearInterval(qrExpiryTimer)
  }

  let timeLeft = expiresIn

  qrExpiryTimer = setInterval(() => {
    timeLeft--

    if (timeLeft <= 0) {
      clearInterval(qrExpiryTimer)
      qrExpires.textContent = "Expired"
      document.getElementById("qr-info").classList.add("hidden")
      document.getElementById("qr-placeholder").innerHTML = `
                <div class="text-gray-400">
                    <i class="fas fa-qrcode text-4xl mb-2"></i>
                    <p class="text-sm">QR Code will appear here</p>
                </div>
            `
      return
    }

    const minutes = Math.floor(timeLeft / 60)
    const seconds = timeLeft % 60
    qrExpires.textContent = `Expires in: ${minutes}:${seconds.toString().padStart(2, "0")}`
  }, 1000)
}

function downloadQRCode() {
  if (!currentQRSession) {
    showError("No QR code to download")
    return
  }

  const link = document.createElement("a")
  link.download = `attendance-qr-${Date.now()}.png`
  // currentQRSession.qr_code is a data URL (data:image/png;base64,...)
  link.href = currentQRSession.qr_code
  link.click()
}

async function refreshAttendance() {
  try {
    const response = await axios.get("/api/teacher/attendance/live")
    displayLiveAttendance(response.data.attendance)
  } catch (error) {
    console.error("Error refreshing attendance:", error)
  }
}

function displayLiveAttendance(attendanceData) {
  const attendanceList = document.getElementById("attendance-list")

  if (!attendanceData || attendanceData.length === 0) {
    attendanceList.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <i class="fas fa-users text-3xl mb-3"></i>
                <p>No attendance data available</p>
            </div>
        `
    return
  }

  attendanceList.innerHTML = attendanceData
    .map((record) => {
      const statusClass =
        record.status === "present"
          ? "bg-green-100 text-green-800"
          : record.status === "late"
            ? "bg-yellow-100 text-yellow-800"
            : "bg-red-100 text-red-800"

      const statusIcon =
        record.status === "present" ? "fa-check-circle" : record.status === "late" ? "fa-clock" : "fa-times-circle"

      const markedTime = record.marked_at ? new Date(record.marked_at).toLocaleTimeString() : "Not marked"

      return `
            <div class="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                <div class="flex items-center">
                    <div class="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center mr-3">
                        <i class="fas fa-user text-gray-600"></i>
                    </div>
                    <div>
                        <h4 class="font-medium text-gray-900">${record.student_name}</h4>
                        <p class="text-sm text-gray-600">${record.class_name} • Roll: ${record.roll_no}</p>
                    </div>
                </div>
                <div class="text-right">
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${statusClass}">
                        <i class="fas ${statusIcon} mr-1"></i>
                        ${record.status || "Absent"}
                    </span>
                    <p class="text-xs text-gray-500 mt-1">${markedTime}</p>
                </div>
            </div>
        `
    })
    .join("")
}

function updateTeacherStats(sessions) {
  document.getElementById("today-classes").textContent = sessions.length

  // Calculate present students (placeholder)
  const totalStudents = sessions.reduce((sum, session) => sum + (session.total_students || 0), 0)
  const presentStudents = sessions.reduce((sum, session) => sum + (session.attendance_count || 0), 0)

  document.getElementById("present-students").textContent = `${presentStudents}/${totalStudents}`

  // Calculate average attendance
  const avgAttendance = totalStudents > 0 ? Math.round((presentStudents / totalStudents) * 100) : 0
  document.getElementById("avg-attendance").textContent = `${avgAttendance}%`

  // Low attendance count (placeholder)
  document.getElementById("low-attendance").textContent = "2"
}

async function openManualAttendance() {
  document.getElementById("manual-attendance-modal").classList.remove("hidden")
}

function closeManualAttendance() {
  document.getElementById("manual-attendance-modal").classList.add("hidden")
  document.getElementById("student-list").innerHTML = ""
}

async function loadStudentList() {
  const sessionSelect = document.getElementById("manual-session-select")
  const sessionId = sessionSelect.value

  if (!sessionId) {
    document.getElementById("student-list").innerHTML = ""
    return
  }

  try {
    const response = await axios.get(`/api/teacher/session/${sessionId}/students`)
    const students = response.data.students

    const studentList = document.getElementById("student-list")
    studentList.innerHTML = students
      .map(
        (student) => `
            <div class="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                <div class="flex items-center">
                    <div class="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center mr-3">
                        <i class="fas fa-user text-gray-600 text-sm"></i>
                    </div>
                    <div>
                        <h4 class="font-medium text-gray-900">${student.name}</h4>
                        <p class="text-sm text-gray-600">Roll: ${student.roll_no}</p>
                    </div>
                </div>
                <div class="flex space-x-2">
                    <label class="flex items-center">
                        <input type="radio" name="attendance_${student.id}" value="present" class="mr-1">
                        <span class="text-sm text-green-600">Present</span>
                    </label>
                    <label class="flex items-center">
                        <input type="radio" name="attendance_${student.id}" value="late" class="mr-1">
                        <span class="text-sm text-yellow-600">Late</span>
                    </label>
                    <label class="flex items-center">
                        <input type="radio" name="attendance_${student.id}" value="absent" class="mr-1" checked>
                        <span class="text-sm text-red-600">Absent</span>
                    </label>
                </div>
            </div>
        `,
      )
      .join("")
  } catch (error) {
    console.error("Error loading student list:", error)
    showError("Failed to load student list")
  }
}

async function saveManualAttendance() {
  const sessionSelect = document.getElementById("manual-session-select")
  const sessionId = sessionSelect.value

  if (!sessionId) {
    showError("Please select a session")
    return
  }

  // Collect attendance data
  const attendanceData = []
  const studentInputs = document.querySelectorAll('[name^="attendance_"]')

  studentInputs.forEach((input) => {
    if (input.checked) {
      const studentId = input.name.split("_")[1]
      attendanceData.push({
        student_id: studentId,
        status: input.value,
      })
    }
  })

  try {
    await axios.post("/api/teacher/attendance/manual", {
      session_id: sessionId,
      attendance: attendanceData,
    })

    showSuccess("Attendance saved successfully!")
    closeManualAttendance()
    refreshAttendance()
  } catch (error) {
    console.error("Error saving attendance:", error)
    showError(error.response?.data?.error || "Failed to save attendance")
  }
}

// --- Camera Attendance Modal Logic ---
document.addEventListener("DOMContentLoaded", function() {
  const cameraBtn = document.getElementById("camera-attendance-btn");
  const cameraModal = document.getElementById("camera-attendance-modal");
  const closeCameraModal = document.getElementById("close-camera-modal");
  const video = document.getElementById("camera-attendance-video");
  const scanBtn = document.getElementById("scan-face-btn");
  const feedback = document.getElementById("camera-attendance-feedback");
  const sessionSelect = document.getElementById("camera-session-select");
  let stream = null;

  if (cameraBtn) {
    cameraBtn.addEventListener("click", async () => {
      cameraModal.classList.remove("hidden");
      // Populate session select (reuse logic from manual attendance)
      const res = await axios.get("/api/teacher/sessions/today");
      sessionSelect.innerHTML = '<option value="">Select a session...</option>';
      res.data.sessions.forEach(s => {
        sessionSelect.innerHTML += `<option value="${s.id}">${s.subject} - ${s.class_name}</option>`;
      });
      // Start webcam
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        video.play();
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
      if (!sessionSelect.value) {
        feedback.textContent = "Select a session first.";
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
          session_id: sessionSelect.value
        });
        if (res.data.match) {
          feedback.textContent = `✅ ${res.data.name} – Attendance Marked`;
        } else {
          feedback.textContent = "Unknown face. Try again.";
        }
      } catch (err) {
        feedback.textContent = err.response?.data?.error || "Recognition failed.";
      }
    });
  }
});

function loadRecentActivity() {
  const activityContainer = document.getElementById("recent-activity")

  const activities = [
    { icon: "fa-qrcode", text: "Generated QR code for Math class", time: "5 minutes ago", color: "text-blue-600" },
    { icon: "fa-user-check", text: "25 students marked present", time: "1 hour ago", color: "text-green-600" },
    { icon: "fa-chart-bar", text: "Generated attendance report", time: "2 hours ago", color: "text-purple-600" },
  ]

  activityContainer.innerHTML = activities
    .map(
      (activity) => `
        <div class="flex items-center p-3 rounded-lg hover:bg-gray-50 transition-colors">
            <i class="fas ${activity.icon} ${activity.color} mr-3"></i>
            <div class="flex-1">
                <p class="text-sm text-gray-900">${activity.text}</p>
                <p class="text-xs text-gray-500">${activity.time}</p>
            </div>
        </div>
    `,
    )
    .join("")
}

function loadAttendanceAlerts() {
  const alertsContainer = document.getElementById("attendance-alerts")

  const alerts = [
    { student: "John Doe", class: "10-A", percentage: "65%", type: "low" },
    { student: "Jane Smith", class: "10-B", percentage: "70%", type: "low" },
  ]

  if (alerts.length === 0) {
    alertsContainer.innerHTML = `
            <div class="text-center py-4 text-gray-500">
                <p class="text-sm">No alerts</p>
            </div>
        `
    return
  }

  alertsContainer.innerHTML = alerts
    .map(
      (alert) => `
        <div class="p-3 bg-red-50 border border-red-200 rounded-lg">
            <div class="flex items-center justify-between">
                <div>
                    <h4 class="font-medium text-red-900">${alert.student}</h4>
                    <p class="text-sm text-red-700">${alert.class} • ${alert.percentage} attendance</p>
                </div>
                <button class="text-red-600 hover:text-red-800 text-sm">
                    <i class="fas fa-bell"></i>
                </button>
            </div>
        </div>
    `,
    )
    .join("")
}

function generateReport() {
  const sessionSelect = document.getElementById('session-select')
  const sessionId = sessionSelect.value
  if (!sessionId) {
    showError('Please select a session to generate report')
    return
  }

  // Trigger download of CSV report
  const url = `/api/teacher/session/${sessionId}/report`
  const link = document.createElement('a')
  link.href = url
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  link.remove()
}

function filterAttendance() {
  // Placeholder for attendance filtering
  refreshAttendance()
}

function showSuccess(message) {
  const successDiv = document.getElementById("success-message")
  document.getElementById("success-text").textContent = message
  successDiv.classList.remove("hidden")

  setTimeout(() => {
    successDiv.classList.add("hidden")
  }, 5000)
}

function showError(message) {
  const errorDiv = document.getElementById("error-message")
  document.getElementById("error-text").textContent = message
  errorDiv.classList.remove("hidden")

  setTimeout(() => {
    errorDiv.classList.add("hidden")
  }, 5000)
}

function showQRGenerator() {
  // Scroll to QR generator section
  document.querySelector(".bg-white.rounded-xl.card-shadow").scrollIntoView({
    behavior: "smooth",
  })
}

// --- Camera Attendance Modal Logic ---
document.addEventListener("DOMContentLoaded", function() {
  const cameraBtn = document.getElementById("camera-attendance-btn");
  const cameraModal = document.getElementById("camera-attendance-modal");
  const closeCameraModal = document.getElementById("close-camera-modal");
  const video = document.getElementById("camera-attendance-video");
  const scanBtn = document.getElementById("scan-face-btn");
  const feedback = document.getElementById("camera-attendance-feedback");
  const sessionSelect = document.getElementById("camera-session-select");
  let stream = null;

  if (cameraBtn) {
    cameraBtn.addEventListener("click", async () => {
      cameraModal.classList.remove("hidden");
      // Populate session select (reuse logic from manual attendance)
      const res = await axios.get("/api/teacher/sessions/today");
      sessionSelect.innerHTML = '<option value="">Select a session...</option>';
      res.data.sessions.forEach(s => {
        sessionSelect.innerHTML += `<option value="${s.id}">${s.subject} - ${s.class_name}</option>`;
      });
      // Start webcam
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        video.play();
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
      if (!sessionSelect.value) {
        feedback.textContent = "Select a session first.";
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
          session_id: sessionSelect.value
        });
        if (res.data.match) {
          feedback.textContent = `✅ ${res.data.name} – Attendance Marked`;
        } else {
          feedback.textContent = "Unknown face. Try again.";
        }
      } catch (err) {
        feedback.textContent = err.response?.data?.error || "Recognition failed.";
      }
    });
  }
});
