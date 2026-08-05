const requestCard = document.getElementById("request-card");
const resetCard = document.getElementById("reset-card");
const subtitle = document.getElementById("subtitle");

let pendingIndexNumber = null;

// --- step 1: request a reset code ---
document.getElementById("request-btn").addEventListener("click", async () => {
  const index_number = document.getElementById("request-index").value.trim();
  const email = document.getElementById("request-email").value.trim();
  const msg = document.getElementById("request-msg");

  if (!index_number || !email) {
    showMessage(msg, "Please fill in both fields.", "error");
    return;
  }

  try {
    const data = await apiRequest("/api/auth/forgot-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ index_number, email }),
    });
    pendingIndexNumber = index_number;
    showMessage(msg, data.message, "success");
    requestCard.classList.add("hidden");
    resetCard.classList.remove("hidden");
    subtitle.textContent = "Enter the code we sent, along with your new password.";
  } catch (err) {
    showMessage(msg, err.message, "error");
  }
});

// --- step 2: submit the code + new password ---
document.getElementById("reset-btn").addEventListener("click", async () => {
  const otp_code = document.getElementById("reset-otp").value.trim();
  const new_password = document.getElementById("reset-password").value;
  const msg = document.getElementById("reset-msg");

  if (!otp_code || !new_password) {
    showMessage(msg, "Enter the code and a new password.", "error");
    return;
  }
  if (new_password.length < 6) {
    showMessage(msg, "Password must be at least 6 characters.", "error");
    return;
  }

  try {
    const data = await apiRequest("/api/auth/reset-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ index_number: pendingIndexNumber, otp_code, new_password }),
    });
    showMessage(msg, data.message + " Redirecting to login...", "success");
    setTimeout(() => { window.location.href = "index.html"; }, 1800);
  } catch (err) {
    showMessage(msg, err.message, "error");
  }
});
