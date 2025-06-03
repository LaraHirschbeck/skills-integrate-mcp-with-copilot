document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  let isTeacherLoggedIn = false;
  
  // Auth related elements
  const loginSection = document.getElementById("login-section");
  const userSection = document.getElementById("user-section");
  const loginBtn = document.getElementById("login-btn");
  const logoutBtn = document.getElementById("logout-btn");
  const loginModal = document.getElementById("login-modal");
  const loginForm = document.getElementById("login-form");
  const userNameSpan = document.getElementById("user-name");

  // Show modal when login button is clicked
  loginBtn.addEventListener("click", () => {
    loginModal.style.display = "block";
  });

  // Close modal when clicking outside
  window.addEventListener("click", (event) => {
    if (event.target === loginModal) {
      loginModal.style.display = "none";
    }
  });

  // Show/hide auth sections
  function showLoginSection() {
    loginSection.style.display = "block";
    userSection.style.display = "none";
    isTeacherLoggedIn = false;
    updateUIForRole();
  }

  function showUserSection(username) {
    loginSection.style.display = "none";
    userSection.style.display = "block";
    userNameSpan.textContent = username;
    isTeacherLoggedIn = true;
    updateUIForRole();
  }

  // Update UI based on role
  function updateUIForRole() {
    const registerBtns = document.querySelectorAll(".register-btn");
    const unregisterBtns = document.querySelectorAll(".unregister-btn");
    
    registerBtns.forEach(btn => {
      btn.style.display = isTeacherLoggedIn ? "inline-block" : "none";
    });
    
    unregisterBtns.forEach(btn => {
      btn.style.display = isTeacherLoggedIn ? "inline-block" : "none";
    });
  }

  // Handle login
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(loginForm);

    try {
      const response = await fetch("/api/login", {
        method: "POST",
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        showUserSection(data.username);
        loginModal.style.display = "none";
        showMessage("Logged in successfully", "success");
      } else {
        const error = await response.json();
        showMessage(error.detail, "error");
      }
    } catch (error) {
      showMessage("Login failed", "error");
      console.error("Login error:", error);
    }
  });

  // Handle logout
  logoutBtn.addEventListener("click", async () => {
    try {
      const response = await fetch("/api/logout", { method: "POST" });
      if (response.ok) {
        showLoginSection();
        showMessage("Logged out successfully", "success");
      } else {
        showMessage("Logout failed", "error");
      }
    } catch (error) {
      showMessage("Logout failed", "error");
      console.error("Logout error:", error);
    }
  });

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";
      activitySelect.innerHTML = "";

      // Add default option to select
      const defaultOption = document.createElement("option");
      defaultOption.value = "";
      defaultOption.textContent = "Select an activity";
      activitySelect.appendChild(defaultOption);

      // Populate activities list and select
      Object.entries(activities).forEach(([name, details]) => {
        // Create activity card
        const card = document.createElement("div");
        card.className = "activity-card";
        card.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Available Spots:</strong> ${details.max_participants - details.participants.length}</p>
          <div class="participants-section">
            <h5>Current Participants:</h5>
            ${details.participants.length > 0 
              ? `<ul>${details.participants.map(email => `
                  <li class="participant">
                    <span class="participant-email">${email}</span>
                    <button class="delete-btn" data-activity="${name}" data-email="${email}">Remove</button>
                  </li>`).join("")}</ul>`
              : "<p>No participants yet</p>"
            }
          </div>
        `;

        // Add event listeners to delete buttons
        const deleteButtons = card.querySelectorAll(".delete-btn");
        deleteButtons.forEach(button => {
          button.addEventListener("click", handleUnregister);
        });

        activitiesList.appendChild(card);

        // Add option to select
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      showMessage("Failed to load activities", "error");
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    event.preventDefault();
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(`/activities/${activity}/unregister?email=${email}`, {
        method: "DELETE"
      });

      if (response.ok) {
        showMessage(`Unregistered ${email} from ${activity}`, "success");
        fetchActivities(); // Refresh the list
      } else {
        const error = await response.json();
        showMessage(error.detail, "error");
      }
    } catch (error) {
      showMessage("Failed to unregister", "error");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(`/activities/${activity}/signup?email=${email}`, {
        method: "POST"
      });

      if (response.ok) {
        showMessage(`Signed up ${email} for ${activity}`, "success");
        signupForm.reset();
        fetchActivities(); // Refresh the list
      } else {
        const error = await response.json();
        showMessage(error.detail, "error");
      }
    } catch (error) {
      showMessage("Failed to sign up", "error");
      console.error("Error signing up:", error);
    }
  });

  function showMessage(text, type) {
    messageDiv.textContent = text;
    messageDiv.className = `message ${type}`;
    messageDiv.classList.remove("hidden");
    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  // Modify register student function to include auth check
  async function registerStudent(activityName, studentEmail) {
    if (!isTeacherLoggedIn) {
      showMessage("Please login as a teacher to register students", "error");
      return;
    }

    try {
      const response = await fetch(`/api/activities/${activityName}/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ student_email: studentEmail }),
      });

      const data = await response.json();
      if (response.ok) {
        showMessage(data.message, "success");
        await fetchActivities(); // Refresh the activities list
      } else {
        showMessage(data.detail, "error");
      }
    } catch (error) {
      showMessage("Failed to register student", "error");
      console.error("Registration error:", error);
    }
  }

  // Modify unregister student function to include auth check
  async function unregisterStudent(activityName, studentEmail) {
    if (!isTeacherLoggedIn) {
      showMessage("Please login as a teacher to unregister students", "error");
      return;
    }

    try {
      const response = await fetch(`/api/activities/${activityName}/unregister`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ student_email: studentEmail }),
      });

      const data = await response.json();
      if (response.ok) {
        showMessage(data.message, "success");
        await fetchActivities(); // Refresh the activities list
      } else {
        showMessage(data.detail, "error");
      }
    } catch (error) {
      showMessage("Failed to unregister student", "error");
      console.error("Unregistration error:", error);
    }
  }

  // Initialize the page
  showLoginSection();
  fetchActivities();
});
