// Shared fetch helper — attaches the JWT automatically and normalizes errors.
const API_BASE = "";

function getToken() {
  return localStorage.getItem("voting_token");
}
function setToken(token) {
  localStorage.setItem("voting_token", token);
}
function clearToken() {
  localStorage.removeItem("voting_token");
}
function getRole() {
  return localStorage.getItem("voting_role");
}
function setRole(role) {
  localStorage.setItem("voting_role", role);
}

async function apiRequest(path, options = {}) {
  const headers = options.headers || {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  let data = {};
  try { data = await response.json(); } catch (e) { /* no body */ }

  if (!response.ok) {
    throw new Error(data.detail || "Something went wrong. Please try again.");
  }
  return data;
}

function showMessage(el, text, type) {
  el.textContent = text;
  el.className = `msg ${type}`;
  el.classList.remove("hidden");
}
