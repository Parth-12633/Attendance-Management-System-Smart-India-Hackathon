// Authentication utilities
// Assumes axios is loaded globally via CDN before this script

class AuthManager {
  constructor() {
    this.token = localStorage.getItem("token") || sessionStorage.getItem("token")
    this.user = JSON.parse(localStorage.getItem("user") || sessionStorage.getItem("user") || "null")
    this.init()
    this.verifyToken() // Verify token on initialization
  }

  init() {
    // Set up axios defaults
    if (this.token) {
      axios.defaults.headers.common["Authorization"] = `Bearer ${this.token}`
    }

    // Update UI based on auth state
    this.updateUI()

    // Set up logout handler
    const logoutBtn = document.getElementById("logout-btn")
    if (logoutBtn) {
      logoutBtn.addEventListener("click", () => this.logout())
    }
  }

  async login(credentials) {
    try {
      const response = await axios.post("/api/auth/login", credentials, {
        withCredentials: true // This is important for handling cookies
      })
      if (!response.data || !response.data.token || !response.data.user) {
        // Backend did not return expected data
        return {
          success: false,
          error: response.data?.error || "Login failed: Invalid server response."
        }
      }
      const { token, user } = response.data

      this.token = token
      this.user = user

      // Store in localStorage for persistence
      localStorage.setItem("token", token)
      localStorage.setItem("user", JSON.stringify(user))

      // Set axios header
      axios.defaults.headers.common["Authorization"] = `Bearer ${token}`

      this.updateUI()
      return { success: true, user }
    } catch (error) {
      let backendMsg = error.response?.data?.error
      if (!backendMsg && error.response && typeof error.response.data === 'string') {
        backendMsg = error.response.data
      }
      return {
        success: false,
        error: backendMsg || error.message || "Login failed",
      }
    }
  }

  async logout() {
    try {
      await axios.post("/api/auth/logout", {}, {
        withCredentials: true
      })
    } catch (error) {
      console.error("Logout error:", error)
    }

    // Clear local storage
    localStorage.removeItem("token")
    localStorage.removeItem("user")
    sessionStorage.removeItem("token")
    sessionStorage.removeItem("user")

    // Clear axios header
    delete axios.defaults.headers.common["Authorization"]

    this.token = null
    this.user = null

    // Redirect to login
    window.location.href = "/login"
  }

  updateUI() {
    const userInfo = document.getElementById("user-info")
    const userName = document.getElementById("user-name")

    if (this.user && userInfo && userName) {
      userInfo.classList.remove("hidden")
      userName.textContent = `${this.user.name} (${this.user.role})`
    }
  }

  isAuthenticated() {
    return !!this.token && !!this.user
  }

  hasRole(role) {
    return this.user && this.user.role === role
  }

  requireAuth() {
    if (!this.isAuthenticated()) {
      window.location.href = "/login"
      return false
    }
    return true
  }

  requireRole(role) {
    if (!this.requireAuth()) return false

    if (!this.hasRole(role)) {
      alert("Access denied: Insufficient permissions")
      return false
    }
    return true
  }

  async verifyToken() {
    if (!this.token) return false

    try {
      const response = await axios.get("/api/auth/verify")
      return response.data.valid
    } catch (error) {
      console.error("Token verification failed:", error)
      this.logout()
      return false
    }
  }
}

// Global auth manager instance
const auth = new AuthManager()

// Utility functions
function showMessage(elementId, message, type = "error") {
  const element = document.getElementById(elementId)
  if (element) {
    element.textContent = message
    element.className = `mt-4 p-3 border rounded-lg ${
      type === "success" ? "bg-green-100 border-green-400 text-green-700" : "bg-red-100 border-red-400 text-red-700"
    }`
    element.classList.remove("hidden")

    // Auto-hide after 5 seconds
    setTimeout(() => {
      element.classList.add("hidden")
    }, 5000)
  }
}

function hideMessage(elementId) {
  const element = document.getElementById(elementId)
  if (element) {
    element.classList.add("hidden")
  }
}

// Redirect based on user role
function redirectToDashboard(user) {
  switch (user.role) {
    case "student":
      window.location.href = "/student-dashboard"
      break
    case "teacher":
      window.location.href = "/teacher-dashboard"
      break
    case "admin":
      window.location.href = "/admin-dashboard"
      break
    default:
      window.location.href = "/"
  }
}

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      auth.logout()
    }
    return Promise.reject(error)
  },
)
