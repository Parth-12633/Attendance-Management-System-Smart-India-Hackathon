// Helper for scanning QR (mobile/web) and sending JWT to server to mark attendance

async function markAttendanceWithToken(token) {
  try {
    const axios = window.axios || null
    if (!axios) {
      console.error('axios not found on window; ensure axios is loaded')
      return { success: false, error: 'axios not available' }
    }

    const res = await axios.post('/api/attendance/mark-qr', { token })
    return { success: true, data: res.data }
  } catch (err) {
    console.error('Error marking attendance', err)
    return { success: false, error: err.response?.data?.error || err.message }
  }
}

// Expose globally for demo pages
window.markAttendanceWithToken = markAttendanceWithToken
