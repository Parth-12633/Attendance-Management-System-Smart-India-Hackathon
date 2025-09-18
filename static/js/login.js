document.addEventListener("DOMContentLoaded", () => {
  // Import AuthManager and redirectToDashboard from auth.js
  // Assumes auth.js is loaded before this script in the HTML
  const studentTab = document.getElementById("student-tab")
  const teacherTab = document.getElementById("teacher-tab")
  const adminTab = document.getElementById("admin-tab")
  const studentForm = document.getElementById("student-form")
  const staffForm = document.getElementById("staff-form")

  let currentLoginType = "student"

  function switchTab(tab, loginType) {
    [studentTab, teacherTab, adminTab].forEach((t) => {
      t.classList.remove("bg-white", "text-indigo-600", "shadow-sm")
      t.classList.add("text-gray-500", "hover:text-gray-700")
    })
    tab.classList.remove("text-gray-500", "hover:text-gray-700")
    tab.classList.add("bg-white", "text-indigo-600", "shadow-sm")
    if (loginType === "student") {
      studentForm.classList.remove("hidden")
      staffForm.classList.add("hidden")
    } else {
      studentForm.classList.add("hidden")
      staffForm.classList.remove("hidden")
    }
    currentLoginType = loginType
    hideMessage("error-message")
    hideMessage("success-message")
  }

  function hideMessage(messageId) {
    const messageElement = document.getElementById(messageId)
    if (messageElement) {
      messageElement.classList.add("hidden")
    }
  }

  function showMessage(messageId, message, type = "error") {
    const messageElement = document.getElementById(messageId)
    if (messageElement) {
      messageElement.classList.remove("hidden")
      messageElement.textContent = message
      messageElement.style.color = type === "success" ? "green" : "red"
    }
  }

  // Use the global auth and redirectToDashboard from auth.js
  studentTab.addEventListener("click", () => switchTab(studentTab, "student"))
  teacherTab.addEventListener("click", () => switchTab(teacherTab, "teacher"))
  adminTab.addEventListener("click", () => switchTab(adminTab, "admin"))

  // Student form submission
  studentForm.addEventListener("submit", async (e) => {
    e.preventDefault()
    const credentials = {
      login_type: "student",
      name: document.getElementById("student-name").value.trim(),
      roll_no: document.getElementById("student-roll").value.trim(),
      division: document.getElementById("student-division").value,
      standard: document.getElementById("student-standard").value,
      password: document.getElementById("student-password").value
    }
    if (!credentials.name || !credentials.roll_no || !credentials.division || !credentials.standard || !credentials.password) {
      showMessage("error-message", "Please fill in all required fields")
      return
    }
    const submitBtn = studentForm.querySelector('button[type="submit"]')
    const originalText = submitBtn.innerHTML
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Logging in...'
    submitBtn.disabled = true
    try {
      const result = await auth.login(credentials)
      if (result.success) {
        showMessage("success-message", "Login successful! Redirecting...", "success")
        setTimeout(() => redirectToDashboard(result.user), 1500)
      } else {
        showMessage("error-message", result.error)
      }
    } catch (error) {
      showMessage("error-message", "An unexpected error occurred")
    } finally {
      submitBtn.innerHTML = originalText
      submitBtn.disabled = false
    }
  })

  // Staff form submission
  staffForm.addEventListener("submit", async (e) => {
    e.preventDefault()
    const credentials = {
      login_type: currentLoginType,
      email: document.getElementById("staff-email").value.trim(),
      password: document.getElementById("staff-password").value,
    }
    if (!credentials.email || !credentials.password) {
      showMessage("error-message", "Please enter both email and password")
      return
    }
    const submitBtn = staffForm.querySelector('button[type="submit"]')
    const originalText = submitBtn.innerHTML
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Logging in...'
    submitBtn.disabled = true
    try {
      const result = await auth.login(credentials)
      if (result.success) {
        showMessage("success-message", "Login successful! Redirecting...", "success")
        setTimeout(() => redirectToDashboard(result.user), 1500)
      } else {
        showMessage("error-message", result.error)
      }
    } catch (error) {
      showMessage("error-message", "An unexpected error occurred")
    } finally {
      submitBtn.innerHTML = originalText
      submitBtn.disabled = false
    }
  })

  // Check if already logged in
  if (auth.isAuthenticated()) {
    redirectToDashboard(auth.user)
  }
})
