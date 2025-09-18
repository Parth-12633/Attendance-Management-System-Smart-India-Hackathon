document.addEventListener("DOMContentLoaded", () => {
  // Tab switching
  const studentTab = document.getElementById("student-tab")
  const teacherTab = document.getElementById("teacher-tab")
  const adminTab = document.getElementById("admin-tab")
  const studentForm = document.getElementById("student-form")
  const teacherForm = document.getElementById("teacher-form")
  const adminForm = document.getElementById("admin-form")

  function switchTab(tab, form) {
    [studentTab, teacherTab, adminTab].forEach((t) => t.classList.remove("bg-white", "text-indigo-600", "shadow-sm"))
    tab.classList.add("bg-white", "text-indigo-600", "shadow-sm")
    studentForm.classList.add("hidden")
    teacherForm.classList.add("hidden")
    adminForm.classList.add("hidden")
    form.classList.remove("hidden")
    hideMessage()
  }

  studentTab.addEventListener("click", () => switchTab(studentTab, studentForm))
  teacherTab.addEventListener("click", () => switchTab(teacherTab, teacherForm))
  adminTab.addEventListener("click", () => switchTab(adminTab, adminForm))

  // Student registration
  studentForm.addEventListener("submit", async (e) => {
    e.preventDefault()
    const data = {
      name: document.getElementById("student-name").value.trim(),
      roll_no: document.getElementById("student-roll").value.trim(),
      division: document.getElementById("student-division").value.trim(),
      standard: document.getElementById("student-standard").value.trim(),
      password: document.getElementById("student-password").value
    }
    await submitRegistration("/api/auth/register/student", data)
  })

  // Teacher registration
  teacherForm.addEventListener("submit", async (e) => {
    e.preventDefault()
    const data = {
      name: document.getElementById("teacher-name").value.trim(),
      email: document.getElementById("teacher-email").value.trim(),
      employee_id: document.getElementById("teacher-employee-id").value.trim(),
      department: document.getElementById("teacher-department").value.trim(),
      password: document.getElementById("teacher-password").value
    }
    await submitRegistration("/api/auth/register/teacher", data)
  })

  // Admin registration
  adminForm.addEventListener("submit", async (e) => {
    e.preventDefault()
    const data = {
      name: document.getElementById("admin-name").value.trim(),
      email: document.getElementById("admin-email").value.trim(),
      password: document.getElementById("admin-password").value
    }
    await submitRegistration("/api/auth/register/admin", data)
  })

  async function submitRegistration(url, data) {
    hideMessage()
    try {
      const response = await axios.post(url, data)
      showMessage("register-success", response.data.message, "success")
    } catch (error) {
      const msg = error.response?.data?.error || "Registration failed"
      showMessage("register-error", msg, "error")
    }
  }

  function showMessage(id, message, type) {
    const el = document.getElementById(id)
    if (el) {
      el.textContent = message
      el.classList.remove("hidden")
      if (type === "success") {
        setTimeout(() => {
          el.classList.add("hidden")
        }, 4000)
      }
    }
  }
  function hideMessage() {
    document.getElementById("register-error").classList.add("hidden")
    document.getElementById("register-success").classList.add("hidden")
  }
})
