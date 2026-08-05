// Handles the login -> OTP -> redirect flow, and registration.

const loginCard = document.getElementById("login-card");
const otpCard = document.getElementById("otp-card");
const registerCard = document.getElementById("register-card");
const subtitle = document.getElementById("subtitle");

let pendingIndexNumber = null; // holds the index number between the login step and the OTP step

// --- view switching ---
document.getElementById("show-register").addEventListener("click", () => {
  loginCard.classList.add("hidden");
  registerCard.classList.remove("hidden");
  subtitle.textContent = "Register using the index number your department has on file.";
});

document.getElementById("show-login").addEventListener("click", () => {
  registerCard.classList.add("hidden");
  loginCard.classList.remove("hidden");
  subtitle.textContent = "Log in with your index number to vote.";
});

// --- login (step 1: password) ---
document.getElementById("login-btn").addEventListener("click", async () => {
  const index_number = document.getElementById("login-index").value.trim();
  const password = document.getElementById("login-password").value;
  const msg = document.getElementById("login-msg");

  if (!index_number || !password) {
    showMessage(msg, "Please fill in both fields.", "error");
    return;
  }

  try {
    const data = await apiRequest("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ index_number, password }),
    });
    pendingIndexNumber = index_number;
    showMessage(msg, data.message, "success");
    loginCard.classList.add("hidden");
    otpCard.classList.remove("hidden");
  } catch (err) {
    showMessage(msg, err.message, "error");
  }
});

// --- login (step 2: OTP) ---
document.getElementById("otp-btn").addEventListener("click", async () => {
  const otp_code = document.getElementById("otp-code").value.trim();
  const msg = document.getElementById("otp-msg");

  if (!otp_code) {
    showMessage(msg, "Enter the code from your email.", "error");
    return;
  }

  try {
    const data = await apiRequest("/api/auth/verify-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ index_number: pendingIndexNumber, otp_code }),
    });
    setToken(data.access_token);
    setRole(data.role);
    window.location.href = data.role === "admin" ? "admin.html" : "ballot.html";
  } catch (err) {
    showMessage(msg, err.message, "error");
  }
});

// --- register ---
document.getElementById("register-btn").addEventListener("click", async () => {
  const level = document.getElementById("reg-level").value;
  const index_number = document.getElementById("reg-index").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const password = document.getElementById("reg-password").value;
  const msg = document.getElementById("register-msg");

  if (!index_number || !email || !password) {
    showMessage(msg, "Please fill in every field.", "error");
    return;
  }

  try {
    const data = await apiRequest("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ level, index_number, email, password }),
    });
    showMessage(msg, data.message + " Redirecting to login...", "success");
    setTimeout(() => {
      registerCard.classList.add("hidden");
      loginCard.classList.remove("hidden");
      subtitle.textContent = "Log in with your index number to vote.";
    }, 1500);
  } catch (err) {
    showMessage(msg, err.message, "error");
  }
});
