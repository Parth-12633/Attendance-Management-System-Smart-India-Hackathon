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

  // --- Face Registration Webcam Logic ---
  const video = document.getElementById("face-video");
  const captureBtn = document.getElementById("capture-face-btn");
  const clearBtn = document.getElementById("clear-faces-btn");
  const thumbnails = document.getElementById("face-thumbnails");
  let faceImages = [];

  if (video && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ video: true })
      .then(stream => {
        video.srcObject = stream;
        video.play();
      })
      .catch(() => {
        video.parentElement.innerHTML = '<span class="text-red-600">Webcam not available</span>';
      });
  }

  if (captureBtn) {
    captureBtn.addEventListener("click", () => {
      if (faceImages.length >= 5) return;
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext("2d").drawImage(video, 0, 0);
      const dataUrl = canvas.toDataURL("image/jpeg");
      faceImages.push(dataUrl);
      const img = document.createElement("img");
      img.src = dataUrl;
      img.width = 48;
      img.height = 36;
      img.className = "rounded border";
      thumbnails.appendChild(img);
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      faceImages = [];
      thumbnails.innerHTML = "";
    });
  }

  // Override student registration to include face upload
  if (studentForm) {
    studentForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (faceImages.length < 3) {
        showMessage("register-error", "Please capture at least 3 face images.", "error");
        return;
      }
      const data = {
        name: document.getElementById("student-name").value.trim(),
        roll_no: document.getElementById("student-roll").value.trim(),
        division: document.getElementById("student-division").value.trim(),
        standard: document.getElementById("student-standard").value.trim(),
        password: document.getElementById("student-password").value
      };
      hideMessage();
      let student_id;
      try {
        const res = await axios.post("/api/auth/register/student", data);
        student_id = res.data.student_id || res.data.id;
      } catch (err) {
        showMessage("register-error", err.response?.data?.error || "Registration failed", "error");
        return;
      }
      // Upload face images
      try {
        await axios.post("/api/ai/register_face", {
          student_id,
          images: faceImages
        });
        showMessage("register-success", "Registration complete! You can now log in.", "success");
        setTimeout(() => window.location.href = "/login", 2000);
      } catch (err) {
        showMessage("register-error", "Face registration failed. Try again.", "error");
      }
    });
  }
})
