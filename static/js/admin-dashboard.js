// Import necessary modules
const auth = require("./auth") // Placeholder for actual import
const axios = require("axios") // Placeholder for actual import

document.addEventListener("DOMContentLoaded", async () => {
  // Check authentication
  if (!auth.requireAuth() || !auth.hasRole("admin")) {
    return
  }

  // Initialize dashboard
  setupTabNavigation()
  setupEventListeners()
  await loadDashboardData()
})

let currentUsersPage = 1
const usersPerPage = 10

function setupTabNavigation() {
  const tabs = ["users", "classes", "reports", "settings"]

  tabs.forEach((tab) => {
    document.getElementById(`${tab}-tab`).addEventListener("click", () => {
      // Update tab styles
      tabs.forEach((t) => {
        const tabElement = document.getElementById(`${t}-tab`)
        const contentElement = document.getElementById(`${t}-content`)

        if (t === tab) {
          tabElement.classList.remove(
            "border-transparent",
            "text-gray-500",
            "hover:text-gray-700",
            "hover:border-gray-300",
          )
          tabElement.classList.add("border-indigo-500", "text-indigo-600")
          contentElement.classList.remove("hidden")
        } else {
          tabElement.classList.add(
            "border-transparent",
            "text-gray-500",
            "hover:text-gray-700",
            "hover:border-gray-300",
          )
          tabElement.classList.remove("border-indigo-500", "text-indigo-600")
          contentElement.classList.add("hidden")
        }
      })

      // Load tab-specific data
      if (tab === "users") {
        loadUsers()
      } else if (tab === "classes") {
        loadClassesAndSubjects()
      }
    })
  })
}

function setupEventListeners() {
  // User Management
  document.getElementById("add-user-btn").addEventListener("click", openAddUserModal)
  document.getElementById("close-add-user-modal").addEventListener("click", closeAddUserModal)
  document.getElementById("cancel-add-user").addEventListener("click", closeAddUserModal)
  document.getElementById("add-user-form").addEventListener("submit", handleAddUser)
  document.getElementById("new-user-role").addEventListener("change", toggleUserFields)

  // User filters and search
  document.getElementById("user-role-filter").addEventListener("change", filterUsers)
  document.getElementById("user-status-filter").addEventListener("change", filterUsers)
  document.getElementById("user-search").addEventListener("input", debounce(searchUsers, 300))

  // Pagination
  document.getElementById("users-prev").addEventListener("click", () => changePage(-1))
  document.getElementById("users-next").addEventListener("click", () => changePage(1))

  // Settings
  document.getElementById("save-settings").addEventListener("click", saveSettings)

  // Reports
  document.getElementById("generate-custom-report").addEventListener("click", generateCustomReport)

  // System actions
  document.getElementById("system-backup-btn").addEventListener("click", initiateBackup)
}

async function loadDashboardData() {
  try {
    // Load system statistics
    const statsResponse = await axios.get("/api/admin/stats")
    updateSystemStats(statsResponse.data)

    // Load users by default
    await loadUsers()
  } catch (error) {
    console.error("Error loading dashboard data:", error)
    showError("Failed to load dashboard data")
  }
}

function updateSystemStats(stats) {
  document.getElementById("total-users").textContent = stats.total_users || 0
  document.getElementById("active-students").textContent = stats.active_students || 0
  document.getElementById("total-teachers").textContent = stats.total_teachers || 0
  document.getElementById("today-sessions").textContent = stats.today_sessions || 0
}

async function loadUsers(page = 1) {
  try {
    const roleFilter = document.getElementById("user-role-filter").value
    const statusFilter = document.getElementById("user-status-filter").value
    const searchQuery = document.getElementById("user-search").value

    const params = new URLSearchParams({
      page: page.toString(),
      per_page: usersPerPage.toString(),
    })

    if (roleFilter) params.append("role", roleFilter)
    if (statusFilter) params.append("status", statusFilter)
    if (searchQuery) params.append("search", searchQuery)

    const response = await axios.get(`/api/admin/users?${params}`)
    const { users, total, page: currentPage, per_page } = response.data

    displayUsers(users)
    updateUsersPagination(total, currentPage, per_page)
  } catch (error) {
    console.error("Error loading users:", error)
    showError("Failed to load users")
  }
}

function displayUsers(users) {
  const tbody = document.getElementById("users-table-body")

  if (!users || users.length === 0) {
    tbody.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-4 text-center text-gray-500">
                    No users found
                </td>
            </tr>
        `
    return
  }

  tbody.innerHTML = users
    .map((user) => {
      const statusClass = user.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
      const statusText = user.is_active ? "Active" : "Inactive"

      return `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <div class="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center mr-4">
                            <i class="fas fa-user text-gray-600"></i>
                        </div>
                        <div>
                            <div class="text-sm font-medium text-gray-900">${user.name}</div>
                            <div class="text-sm text-gray-500">${user.email || "N/A"}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        ${user.role}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusClass}">
                        ${statusText}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${user.last_login ? new Date(user.last_login).toLocaleDateString() : "Never"}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div class="flex space-x-2">
                        <button onclick="editUser(${user.id})" class="text-indigo-600 hover:text-indigo-900">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="toggleUserStatus(${user.id}, ${!user.is_active})" class="text-${user.is_active ? "red" : "green"}-600 hover:text-${user.is_active ? "red" : "green"}-900">
                            <i class="fas fa-${user.is_active ? "ban" : "check"}"></i>
                        </button>
                        <button onclick="deleteUser(${user.id})" class="text-red-600 hover:text-red-900">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `
    })
    .join("")
}

function updateUsersPagination(total, currentPage, perPage) {
  const totalPages = Math.ceil(total / perPage)
  const startItem = (currentPage - 1) * perPage + 1
  const endItem = Math.min(currentPage * perPage, total)

  document.getElementById("users-showing").textContent = `${startItem}-${endItem}`
  document.getElementById("users-total").textContent = total

  document.getElementById("users-prev").disabled = currentPage <= 1
  document.getElementById("users-next").disabled = currentPage >= totalPages

  currentUsersPage = currentPage
}

function changePage(direction) {
  const newPage = currentUsersPage + direction
  if (newPage >= 1) {
    loadUsers(newPage)
  }
}

function filterUsers() {
  loadUsers(1) // Reset to first page when filtering
}

function searchUsers() {
  loadUsers(1) // Reset to first page when searching
}

function openAddUserModal() {
  document.getElementById("add-user-modal").classList.remove("hidden")
}

function closeAddUserModal() {
  document.getElementById("add-user-modal").classList.add("hidden")
  document.getElementById("add-user-form").reset()
  toggleUserFields() // Reset field visibility
}

function toggleUserFields() {
  const role = document.getElementById("new-user-role").value
  const emailField = document.getElementById("email-field")
  const studentFields = document.getElementById("student-fields")
  const teacherFields = document.getElementById("teacher-fields")

  // Hide all fields first
  emailField.classList.add("hidden")
  studentFields.classList.add("hidden")
  teacherFields.classList.add("hidden")

  // Show relevant fields based on role
  if (role === "teacher" || role === "admin") {
    emailField.classList.remove("hidden")
    document.getElementById("new-user-email").required = true
  } else {
    document.getElementById("new-user-email").required = false
  }

  if (role === "student") {
    studentFields.classList.remove("hidden")
  } else if (role === "teacher") {
    teacherFields.classList.remove("hidden")
  }
}

async function handleAddUser(e) {
  e.preventDefault()

  const formData = {
    name: document.getElementById("new-user-name").value,
    role: document.getElementById("new-user-role").value,
  }

  // Add role-specific data
  if (formData.role === "teacher" || formData.role === "admin") {
    formData.email = document.getElementById("new-user-email").value
  }

  if (formData.role === "student") {
    formData.roll_no = document.getElementById("new-student-roll").value
    formData.division = document.getElementById("new-student-division").value
    formData.standard = document.getElementById("new-student-standard").value
  } else if (formData.role === "teacher") {
    formData.employee_id = document.getElementById("new-teacher-employee-id").value
    formData.department = document.getElementById("new-teacher-department").value
  }

  try {
    await axios.post("/api/admin/users", formData)
    showSuccess("User added successfully!")
    closeAddUserModal()
    loadUsers(currentUsersPage)
  } catch (error) {
    console.error("Error adding user:", error)
    showError(error.response?.data?.error || "Failed to add user")
  }
}

async function editUser(userId) {
  // Placeholder for edit user functionality
  showSuccess("Edit user functionality coming soon!")
}

async function toggleUserStatus(userId, newStatus) {
  try {
    await axios.patch(`/api/admin/users/${userId}`, {
      is_active: newStatus,
    })
    showSuccess(`User ${newStatus ? "activated" : "deactivated"} successfully!`)
    loadUsers(currentUsersPage)
  } catch (error) {
    console.error("Error updating user status:", error)
    showError("Failed to update user status")
  }
}

async function deleteUser(userId) {
  if (!confirm("Are you sure you want to delete this user? This action cannot be undone.")) {
    return
  }

  try {
    await axios.delete(`/api/admin/users/${userId}`)
    showSuccess("User deleted successfully!")
    loadUsers(currentUsersPage)
  } catch (error) {
    console.error("Error deleting user:", error)
    showError("Failed to delete user")
  }
}

async function loadClassesAndSubjects() {
  try {
    // Load classes
    const classesResponse = await axios.get("/api/admin/classes")
    displayClasses(classesResponse.data.classes)

    // Load subjects
    const subjectsResponse = await axios.get("/api/admin/subjects")
    displaySubjects(subjectsResponse.data.subjects)
  } catch (error) {
    console.error("Error loading classes and subjects:", error)
    showError("Failed to load classes and subjects")
  }
}

function displayClasses(classes) {
  const container = document.getElementById("classes-list")

  if (!classes || classes.length === 0) {
    container.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <p>No classes found</p>
            </div>
        `
    return
  }

  container.innerHTML = classes
    .map(
      (cls) => `
        <div class="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <div>
                <h4 class="font-medium text-gray-900">${cls.standard}-${cls.division}</h4>
                <p class="text-sm text-gray-600">Academic Year: ${cls.academic_year}</p>
            </div>
            <div class="flex space-x-2">
                <button onclick="editClass(${cls.id})" class="text-indigo-600 hover:text-indigo-900">
                    <i class="fas fa-edit"></i>
                </button>
                <button onclick="deleteClass(${cls.id})" class="text-red-600 hover:text-red-900">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `,
    )
    .join("")
}

function displaySubjects(subjects) {
  const container = document.getElementById("subjects-list")

  if (!subjects || subjects.length === 0) {
    container.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <p>No subjects found</p>
            </div>
        `
    return
  }

  container.innerHTML = subjects
    .map(
      (subject) => `
        <div class="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <div>
                <h4 class="font-medium text-gray-900">${subject.name}</h4>
                <p class="text-sm text-gray-600">Code: ${subject.code}</p>
            </div>
            <div class="flex space-x-2">
                <button onclick="editSubject(${subject.id})" class="text-indigo-600 hover:text-indigo-900">
                    <i class="fas fa-edit"></i>
                </button>
                <button onclick="deleteSubject(${subject.id})" class="text-red-600 hover:text-red-900">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `,
    )
    .join("")
}

async function saveSettings() {
  const settings = {
    school_name: document.getElementById("school-name").value,
    academic_year: document.getElementById("academic-year").value,
    attendance_threshold: document.getElementById("attendance-threshold").value,
    qr_expiry: document.getElementById("qr-expiry").value,
    session_timeout: document.getElementById("session-timeout").value,
  }

  try {
    await axios.post("/api/admin/settings", settings)
    showSuccess("Settings saved successfully!")
  } catch (error) {
    console.error("Error saving settings:", error)
    showError("Failed to save settings")
  }
}

async function generateCustomReport() {
  const reportData = {
    start_date: document.getElementById("report-start-date").value,
    end_date: document.getElementById("report-end-date").value,
    type: document.getElementById("report-type").value,
    format: document.getElementById("report-format").value,
  }

  if (!reportData.start_date || !reportData.end_date) {
    showError("Please select date range")
    return
  }

  try {
    const response = await axios.post("/api/admin/reports/generate", reportData, {
      responseType: "blob",
    })

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement("a")
    link.href = url
    link.setAttribute("download", `report-${Date.now()}.${reportData.format}`)
    document.body.appendChild(link)
    link.click()
    link.remove()

    showSuccess("Report generated successfully!")
  } catch (error) {
    console.error("Error generating report:", error)
    showError("Failed to generate report")
  }
}

async function initiateBackup() {
  if (!confirm("This will create a backup of all system data. Continue?")) {
    return
  }

  try {
    const response = await axios.post("/api/admin/backup", {}, { responseType: "blob" })

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement("a")
    link.href = url
    link.setAttribute("download", `backup-${new Date().toISOString().split("T")[0]}.sql`)
    document.body.appendChild(link)
    link.click()
    link.remove()

    showSuccess("Backup created successfully!")
  } catch (error) {
    console.error("Error creating backup:", error)
    showError("Failed to create backup")
  }
}

// Utility functions
function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
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

// Placeholder functions for future implementation
function editClass(classId) {
  showSuccess("Edit class functionality coming soon!")
}

function deleteClass(classId) {
  showSuccess("Delete class functionality coming soon!")
}

function editSubject(subjectId) {
  showSuccess("Edit subject functionality coming soon!")
}

function deleteSubject(subjectId) {
  showSuccess("Delete subject functionality coming soon!")
}
