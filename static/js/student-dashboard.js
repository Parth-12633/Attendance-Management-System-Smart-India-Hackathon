
// Assumes auth and axios are loaded globally via CDN and auth.js
// If you use QR scanning, ensure jsQR is loaded via CDN in your HTML as well

document.addEventListener("DOMContentLoaded", async () => {
  // Check authentication
  if (!auth.requireAuth() || !auth.hasRole("student")) {
    return
  }

  // Initialize dashboard
  await initializeDashboard()

  // Set up QR scanner
  setupQRScanner()

  // Load dashboard data
  loadDashboardData()

  // Set current date
  document.getElementById("current-date").textContent = new Date().toLocaleDateString()
})

async function initializeDashboard() {
  const user = auth.user
  if (user) {
    document.getElementById("welcome-message").textContent = `Welcome back, ${user.name}!`
    document.getElementById("student-info").textContent =
      `Class ${user.standard}-${user.division} • Roll No: ${user.roll_no}`
  }
}

async function loadDashboardData() {
  try {
    // Load today's sessions
    const sessionsResponse = await axios.get("/api/attendance/sessions/today")
    displayTodaySchedule(sessionsResponse.data.sessions)

    // Update stats
    updateAttendanceStats(sessionsResponse.data.sessions)

    // Load recent activity
    loadRecentActivity()
  } catch (error) {
    console.error("Error loading dashboard data:", error)
    showError("Failed to load dashboard data")
  }
}

function displayTodaySchedule(sessions) {
  const scheduleContainer = document.getElementById("today-schedule")

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

      const statusClass =
        session.attendance_status === "present"
          ? "bg-green-100 text-green-800"
          : session.attendance_status === "late"
            ? "bg-yellow-100 text-yellow-800"
            : "bg-red-100 text-red-800"

      const statusIcon =
        session.attendance_status === "present"
          ? "fa-check-circle"
          : session.attendance_status === "late"
            ? "fa-clock"
            : "fa-times-circle"

      return `
            <div class="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                <div class="flex items-center">
                    <div class="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mr-4">
                        <i class="fas fa-book text-indigo-600"></i>
                    </div>
                    <div>
                        <h4 class="font-semibold text-gray-900">${session.subject}</h4>
                        <p class="text-sm text-gray-600">${session.teacher} • ${startTime}</p>
                    </div>
                </div>
                <div class="text-right">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusClass}">
                        <i class="fas ${statusIcon} mr-1"></i>
                        ${session.attendance_status || "Absent"}
                    </span>
                    ${session.marked_at ? `<p class="text-xs text-gray-500 mt-1">Marked at ${new Date(session.marked_at).toLocaleTimeString()}</p>` : ""}
                </div>
            </div>
        `
    })
    .join("")
}

function updateAttendanceStats(sessions) {
  const presentToday = sessions.filter((s) => s.attendance_status === "present").length
  const totalToday = sessions.length

  document.getElementById("present-count").textContent = `${presentToday}/${totalToday}`

  // Calculate percentage
  const percentage = totalToday > 0 ? Math.round((presentToday / totalToday) * 100) : 0
  document.getElementById("overall-percentage").textContent = `${percentage}%`

  // Placeholder values for week attendance and pending tasks
  document.getElementById("week-attendance").textContent = "85%"
  document.getElementById("pending-tasks").textContent = "3"
}

function setupQRScanner() {
  const scanBtn = document.getElementById("scan-qr-btn")
  const stopBtn = document.getElementById("stop-scan-btn")
  const scanner = document.getElementById("qr-scanner")
  const video = document.getElementById("qr-video")
  const manualSubmit = document.getElementById("submit-manual-qr")

  let stream = null
  let scanning = false

  scanBtn.addEventListener("click", startQRScanner)
  stopBtn.addEventListener("click", stopQRScanner)
  manualSubmit.addEventListener("click", submitManualQR)

  async function startQRScanner() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
      })
      video.srcObject = stream
      scanner.classList.remove("hidden")
      scanBtn.classList.add("hidden")
      scanning = true

      // Start scanning for QR codes
      scanForQRCode()
    } catch (error) {
      console.error("Error accessing camera:", error)
      showError("Unable to access camera. Please check permissions.")
    }
  }

  function stopQRScanner() {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop())
      stream = null
    }
    scanner.classList.add("hidden")
    scanBtn.classList.remove("hidden")
    scanning = false
  }

  function scanForQRCode() {
    if (!scanning) return

    const canvas = document.createElement("canvas")
    const context = canvas.getContext("2d")

    if (video.readyState === video.HAVE_ENOUGH_DATA) {
      canvas.height = video.videoHeight
      canvas.width = video.videoWidth
      context.drawImage(video, 0, 0, canvas.width, canvas.height)

      const imageData = context.getImageData(0, 0, canvas.width, canvas.height)
      const code = jsQR(imageData.data, imageData.width, imageData.height)

      if (code) {
        processQRCode(code.data)
        stopQRScanner()
        return
      }
    }

    requestAnimationFrame(scanForQRCode)
  }

  async function submitManualQR() {
    const qrInput = document.getElementById("manual-qr-input")
    const qrCode = qrInput.value.trim()

    if (!qrCode) {
      showError("Please enter a QR code")
      return
    }

    await processQRCode(qrCode)
    qrInput.value = ""
  }

  async function processQRCode(qrData) {
    try {
      // Extract token from QR data (format: "attendance:token:timetable_id")
      const parts = qrData.split(":")
      if (parts.length !== 3 || parts[0] !== "attendance") {
        showError("Invalid QR code format")
        return
      }

      const qrToken = parts[1]

      // Submit attendance
      const response = await axios.post("/api/attendance/mark-qr", {
        qr_token: qrToken,
      })

      showSuccess("Attendance marked successfully!")

      // Refresh dashboard data
      setTimeout(() => {
        loadDashboardData()
      }, 1000)
    } catch (error) {
      console.error("Error marking attendance:", error)
      const errorMessage = error.response?.data?.error || "Failed to mark attendance"
      showError(errorMessage)
    }
  }
}

async function loadRecentActivity() {
  // Placeholder for recent activity
  const activityContainer = document.getElementById("recent-activity")

  const activities = [
    { icon: "fa-check-circle", text: "Marked present for Mathematics", time: "2 hours ago", color: "text-green-600" },
    { icon: "fa-tasks", text: "Completed Physics assignment", time: "1 day ago", color: "text-blue-600" },
    { icon: "fa-clock", text: "Late arrival for Chemistry", time: "2 days ago", color: "text-yellow-600" },
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

function showSuccess(message) {
  const successDiv = document.getElementById("attendance-success")
  successDiv.querySelector("span").textContent = message
  successDiv.classList.remove("hidden")

  setTimeout(() => {
    successDiv.classList.add("hidden")
  }, 5000)
}

function showError(message) {
  const errorDiv = document.getElementById("attendance-error")
  document.getElementById("error-text").textContent = message
  errorDiv.classList.remove("hidden")

  setTimeout(() => {
    errorDiv.classList.add("hidden")
  }, 5000)
}
