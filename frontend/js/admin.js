// Guard: only accessible if logged in AND the stored role is admin
if (!getToken()) window.location.href = "index.html";
if (getRole() !== "admin") window.location.href = "ballot.html";

document.getElementById("logout-btn").addEventListener("click", () => {
  clearToken();
  window.location.href = "index.html";
});

// --- election timing ---
async function loadElectionSettings() {
  try {
    const data = await apiRequest("/api/admin/election-settings");
    document.getElementById("voting-status").textContent = data.voting_open ? "OPEN" : "CLOSED";
    if (data.opens_at) document.getElementById("opens-at-input").value = toLocalInputValue(data.opens_at);
    if (data.closes_at) document.getElementById("closes-at-input").value = toLocalInputValue(data.closes_at);
  } catch (err) {
    document.getElementById("voting-status").textContent = "unknown";
  }
}

// datetime-local inputs need "YYYY-MM-DDTHH:MM" with no timezone suffix
function toLocalInputValue(isoString) {
  return isoString.slice(0, 16);
}

document.getElementById("election-settings-btn").addEventListener("click", async () => {
  const opens_at = document.getElementById("opens-at-input").value;
  const closes_at = document.getElementById("closes-at-input").value;
  const msg = document.getElementById("election-settings-msg");

  const body = {};
  if (opens_at) body.opens_at = opens_at;
  if (closes_at) body.closes_at = closes_at;

  try {
    const data = await apiRequest("/api/admin/election-settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    document.getElementById("voting-status").textContent = data.voting_open ? "OPEN" : "CLOSED";
    showMessage(msg, "Election timing saved (Ghana time).", "success");
  } catch (err) {
    showMessage(msg, err.message, "error");
  }
});

// --- roster upload ---
document.getElementById("roster-upload-btn").addEventListener("click", async () => {
  const fileInput = document.getElementById("roster-file");
  const msg = document.getElementById("roster-msg");
  if (!fileInput.files.length) {
    showMessage(msg, "Choose a CSV file first.", "error");
    return;
  }
  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  try {
    const data = await apiRequest("/api/admin/roster/upload", { method: "POST", body: formData });
    showMessage(msg, data.message, "success");
  } catch (err) {
    showMessage(msg, err.message, "error");
  }
});

// --- create portfolio ---
document.getElementById("portfolio-btn").addEventListener("click", async () => {
  const title = document.getElementById("portfolio-title").value.trim();
  const msg = document.getElementById("portfolio-msg");
  if (!title) { showMessage(msg, "Enter a portfolio title.", "error"); return; }

  try {
    await apiRequest("/api/admin/portfolios", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    });
    showMessage(msg, "Portfolio created.", "success");
    document.getElementById("portfolio-title").value = "";
    loadPortfolios();
  } catch (err) {
    showMessage(msg, err.message, "error");
  }
});

// --- populate portfolio dropdown for candidate form, AND a deletable list ---
async function loadPortfolios() {
  const select = document.getElementById("candidate-portfolio");
  const list = document.getElementById("portfolio-list");
  try {
    const portfolios = await apiRequest("/api/admin/portfolios");
    select.innerHTML = portfolios.map((p) => `<option value="${p.id}">${p.title}</option>`).join("");

    if (portfolios.length === 0) {
      list.innerHTML = "<p class='subtitle'>No portfolios yet.</p>";
      return;
    }

    list.innerHTML = "";
    portfolios.forEach((p) => {
      const row = document.createElement("div");
      row.style.display = "flex";
      row.style.justifyContent = "space-between";
      row.style.alignItems = "center";
      row.style.padding = "8px 0";
      row.style.borderBottom = "1px solid var(--border)";
      row.innerHTML = `<span>${p.title}</span>`;

      const deleteBtn = document.createElement("button");
      deleteBtn.textContent = "Delete";
      deleteBtn.className = "secondary";
      deleteBtn.style.width = "auto";
      deleteBtn.style.margin = "0";
      deleteBtn.style.padding = "6px 12px";
      deleteBtn.style.fontSize = "12px";
      deleteBtn.addEventListener("click", () => deletePortfolio(p.id, p.title));

      row.appendChild(deleteBtn);
      list.appendChild(row);
    });
  } catch (err) {
    select.innerHTML = "<option>Could not load portfolios</option>";
  }
}

async function deletePortfolio(id, title) {
  const confirmed = window.confirm(
    `Delete "${title}"? This also deletes its candidates and any votes already cast for it. This cannot be undone.`
  );
  if (!confirmed) return;

  try {
    await apiRequest(`/api/admin/portfolios/${id}`, { method: "DELETE" });
    loadPortfolios();
    loadResults();
  } catch (err) {
    alert(err.message);
  }
}

// --- add candidate (multipart form, since photo upload is involved) ---
document.getElementById("candidate-btn").addEventListener("click", async () => {
  const portfolio_id = document.getElementById("candidate-portfolio").value;
  const name = document.getElementById("candidate-name").value.trim();
  const bio = document.getElementById("candidate-bio").value.trim();
  const photoInput = document.getElementById("candidate-photo");
  const msg = document.getElementById("candidate-msg");

  if (!portfolio_id || !name) {
    showMessage(msg, "Portfolio and name are required.", "error");
    return;
  }

  const formData = new FormData();
  formData.append("portfolio_id", portfolio_id);
  formData.append("name", name);
  formData.append("bio", bio);
  if (photoInput.files.length) formData.append("photo", photoInput.files[0]);

  try {
    await apiRequest("/api/admin/candidates", { method: "POST", body: formData });
    showMessage(msg, "Candidate added.", "success");
    document.getElementById("candidate-name").value = "";
    document.getElementById("candidate-bio").value = "";
    photoInput.value = "";
    loadResults();
  } catch (err) {
    showMessage(msg, err.message, "error");
  }
});

const ICON_VOTERS = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
const ICON_VOTED = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4" stroke-linecap="round" stroke-linejoin="round"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

// --- live results ---
async function loadResults() {
  const card = document.getElementById("results-card");
  const statRow = document.getElementById("stat-row");
  try {
    const data = await apiRequest("/api/admin/results");

    statRow.innerHTML = `
      <div class="stat-box">
        <div class="stat-icon accent">${ICON_VOTERS}</div>
        <div><div class="stat-value">${data.total_voters}</div><div class="stat-label">Registered Voters</div></div>
      </div>
      <div class="stat-box">
        <div class="stat-icon deep">${ICON_VOTED}</div>
        <div><div class="stat-value">${data.total_votes_cast}</div><div class="stat-label">Votes Cast</div></div>
      </div>`;

    if (data.portfolios.length === 0) {
      card.innerHTML = "<p class='subtitle'>No portfolios created yet.</p>";
      return;
    }

    card.innerHTML = "";
    data.portfolios.forEach((portfolio) => {
      const block = document.createElement("div");
      block.className = "portfolio-block";
      block.style.boxShadow = "none";
      block.style.border = "none";
      block.style.padding = "0 0 8px";

      const title = document.createElement("div");
      title.className = "portfolio-title";
      title.textContent = portfolio.title;
      block.appendChild(title);

      if (portfolio.is_referendum) {
        const candidate = portfolio.candidates[0];
        const total = Math.max(1, portfolio.yes_votes + portfolio.no_votes);

        const tallyRow = document.createElement("div");
        tallyRow.className = "results-tally-row";
        tallyRow.innerHTML = `
          <div class="tally-item">
            <img class="candidate-photo" src="${candidate.photo_url || ''}" onerror="this.style.opacity=0">
            <div class="tally-name">${candidate.name}</div>
          </div>`;
        block.appendChild(tallyRow);

        [{ label: "Yes", count: portfolio.yes_votes }, { label: "No", count: portfolio.no_votes }].forEach(({ label, count }) => {
          const pct = Math.round((count / total) * 100);
          const row = document.createElement("div");
          row.className = "bar-row";
          row.innerHTML = `
            <div class="bar-label"><span>${label}</span><span class="count">${count}</span></div>
            <div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div>`;
          block.appendChild(row);
        });

        card.appendChild(block);
        return;
      }

      const tallyRow = document.createElement("div");
      tallyRow.className = "results-tally-row";
      portfolio.candidates.forEach((c) => {
        tallyRow.innerHTML += `
          <div class="tally-item">
            <img class="candidate-photo" src="${c.photo_url || ''}" onerror="this.style.opacity=0">
            <div class="tally-name">${c.name}</div>
            <div class="tally-count">${c.votes} vote(s)</div>
          </div>`;
      });
      block.appendChild(tallyRow);

      const maxVotes = Math.max(1, ...portfolio.candidates.map((c) => c.votes));
      portfolio.candidates.forEach((candidate) => {
        const pct = Math.round((candidate.votes / maxVotes) * 100);
        const row = document.createElement("div");
        row.className = "bar-row";
        row.innerHTML = `
          <div class="bar-label"><span>${candidate.name}</span><span class="count">${candidate.votes}</span></div>
          <div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div>`;
        block.appendChild(row);
      });

      card.appendChild(block);
    });
  } catch (err) {
    card.innerHTML = `<div class="msg error">${err.message}</div>`;
  }
}

loadElectionSettings();
loadPortfolios();
loadResults();
setInterval(loadResults, 8000); // auto-refresh so the admin sees turnout update live
