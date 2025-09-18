class AIRecommendations {
  constructor() {
    this.apiBase = "/api/ai"
    this.init()
  }

  init() {
    this.loadRecommendations()
    this.setupEventListeners()
  }

  setupEventListeners() {
    // Refresh recommendations button
    const refreshBtn = document.getElementById("refresh-recommendations")
    if (refreshBtn) {
      refreshBtn.addEventListener("click", () => this.loadRecommendations())
    }
  }

  async loadRecommendations() {
    try {
      const token = localStorage.getItem("token")
      const response = await fetch(`${this.apiBase}/recommendations`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      })

      if (response.ok) {
        const data = await response.json()
        this.displayRecommendations(data)
      } else {
        console.error("Failed to load recommendations")
      }
    } catch (error) {
      console.error("Error loading recommendations:", error)
    }
  }

  displayRecommendations(data) {
    const container = document.getElementById("recommendations-container")
    if (!container) return

    let html = ""

    // Display recommendations
    if (data.recommendations && data.recommendations.length > 0) {
      html += '<div class="space-y-4">'

      data.recommendations.forEach((rec) => {
        const priorityColor = this.getPriorityColor(rec.priority)
        const typeIcon = this.getTypeIcon(rec.type)

        html += `
                    <div class="bg-white rounded-lg shadow-md p-4 border-l-4 ${priorityColor}">
                        <div class="flex items-start space-x-3">
                            <div class="flex-shrink-0">
                                ${typeIcon}
                            </div>
                            <div class="flex-1">
                                <h4 class="font-semibold text-gray-900">${rec.category}</h4>
                                <p class="text-gray-600 mt-1">${rec.message}</p>
                                <p class="text-sm text-blue-600 mt-2 font-medium">${rec.action}</p>
                            </div>
                            <span class="px-2 py-1 text-xs font-medium rounded-full ${this.getPriorityBadge(rec.priority)}">
                                ${rec.priority.toUpperCase()}
                            </span>
                        </div>
                    </div>
                `
      })

      html += "</div>"
    } else {
      html = `
                <div class="text-center py-8">
                    <div class="text-green-500 text-4xl mb-4">✓</div>
                    <h3 class="text-lg font-semibold text-gray-900">All Good!</h3>
                    <p class="text-gray-600">No recommendations at this time. Keep up the great work!</p>
                </div>
            `
    }

    container.innerHTML = html

    // Display charts if data is available
    if (data.trends) {
      this.displayTrendsChart(data.trends)
    }

    if (data.subject_stats) {
      this.displaySubjectChart(data.subject_stats)
    }
  }

  getPriorityColor(priority) {
    switch (priority) {
      case "high":
        return "border-red-500"
      case "medium":
        return "border-yellow-500"
      case "low":
        return "border-green-500"
      default:
        return "border-blue-500"
    }
  }

  getPriorityBadge(priority) {
    switch (priority) {
      case "high":
        return "bg-red-100 text-red-800"
      case "medium":
        return "bg-yellow-100 text-yellow-800"
      case "low":
        return "bg-green-100 text-green-800"
      default:
        return "bg-blue-100 text-blue-800"
    }
  }

  getTypeIcon(type) {
    switch (type) {
      case "warning":
      case "subject_warning":
      case "trend_warning":
        return '<div class="w-6 h-6 bg-red-100 rounded-full flex items-center justify-center"><span class="text-red-600 text-sm">⚠</span></div>'
      case "positive":
        return '<div class="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center"><span class="text-green-600 text-sm">↗</span></div>'
      case "achievement":
        return '<div class="w-6 h-6 bg-yellow-100 rounded-full flex items-center justify-center"><span class="text-yellow-600 text-sm">★</span></div>'
      default:
        return '<div class="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center"><span class="text-blue-600 text-sm">i</span></div>'
    }
  }

  displayTrendsChart(trends) {
    const canvas = document.getElementById("trends-chart")
    if (!canvas || !trends.length) return

    const ctx = canvas.getContext("2d")
    const dates = trends.map((t) => new Date(t.date).toLocaleDateString())
    const percentages = trends.map((t) => t.percentage)

    // Simple line chart implementation
    this.drawLineChart(ctx, dates, percentages, "Attendance Trend")
  }

  displaySubjectChart(subjects) {
    const canvas = document.getElementById("subjects-chart")
    if (!canvas || !subjects.length) return

    const ctx = canvas.getContext("2d")
    const subjectNames = subjects.map((s) => s.subject)
    const percentages = subjects.map((s) => s.percentage)

    // Simple bar chart implementation
    this.drawBarChart(ctx, subjectNames, percentages, "Subject-wise Attendance")
  }

  drawLineChart(ctx, labels, data, title) {
    const canvas = ctx.canvas
    const width = canvas.width
    const height = canvas.height
    const padding = 40

    ctx.clearRect(0, 0, width, height)

    // Draw title
    ctx.fillStyle = "#374151"
    ctx.font = "16px Arial"
    ctx.textAlign = "center"
    ctx.fillText(title, width / 2, 20)

    // Calculate scales
    const maxValue = Math.max(...data, 100)
    const minValue = Math.min(...data, 0)
    const xStep = (width - 2 * padding) / (labels.length - 1)
    const yScale = (height - 2 * padding - 20) / (maxValue - minValue)

    // Draw axes
    ctx.strokeStyle = "#E5E7EB"
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(padding, padding + 20)
    ctx.lineTo(padding, height - padding)
    ctx.lineTo(width - padding, height - padding)
    ctx.stroke()

    // Draw data line
    ctx.strokeStyle = "#3B82F6"
    ctx.lineWidth = 2
    ctx.beginPath()

    data.forEach((value, index) => {
      const x = padding + index * xStep
      const y = height - padding - (value - minValue) * yScale

      if (index === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    })

    ctx.stroke()

    // Draw data points
    ctx.fillStyle = "#3B82F6"
    data.forEach((value, index) => {
      const x = padding + index * xStep
      const y = height - padding - (value - minValue) * yScale

      ctx.beginPath()
      ctx.arc(x, y, 3, 0, 2 * Math.PI)
      ctx.fill()
    })
  }

  drawBarChart(ctx, labels, data, title) {
    const canvas = ctx.canvas
    const width = canvas.width
    const height = canvas.height
    const padding = 40

    ctx.clearRect(0, 0, width, height)

    // Draw title
    ctx.fillStyle = "#374151"
    ctx.font = "16px Arial"
    ctx.textAlign = "center"
    ctx.fillText(title, width / 2, 20)

    const maxValue = Math.max(...data, 100)
    const barWidth = ((width - 2 * padding) / labels.length) * 0.8
    const barSpacing = ((width - 2 * padding) / labels.length) * 0.2

    data.forEach((value, index) => {
      const x = padding + index * (barWidth + barSpacing)
      const barHeight = (value / maxValue) * (height - 2 * padding - 20)
      const y = height - padding - barHeight

      // Color based on percentage
      if (value >= 75) {
        ctx.fillStyle = "#10B981" // Green
      } else if (value >= 60) {
        ctx.fillStyle = "#F59E0B" // Yellow
      } else {
        ctx.fillStyle = "#EF4444" // Red
      }

      ctx.fillRect(x, y, barWidth, barHeight)

      // Draw percentage text
      ctx.fillStyle = "#374151"
      ctx.font = "12px Arial"
      ctx.textAlign = "center"
      ctx.fillText(`${value.toFixed(1)}%`, x + barWidth / 2, y - 5)
    })
  }
}

// Initialize AI recommendations when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("recommendations-container")) {
    new AIRecommendations()
  }
})
