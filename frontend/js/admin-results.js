// Guard: only accessible if logged in AND the stored role is admin
if (!getToken()) window.location.href = "index.html";
if (getRole() !== "admin") window.location.href = "ballot.html";

document.getElementById("logout-btn").addEventListener("click", () => {
  clearToken();
  window.location.href = "index.html";
});

document.getElementById("back-btn").addEventListener("click", () => {
  window.location.href = "admin.html";
});

const ICON_VOTERS = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
const ICON_VOTED = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4" stroke-linecap="round" stroke-linejoin="round"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
const ICON_TURNOUT = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18" stroke-linecap="round" stroke-linejoin="round"/><path d="M7 15l4-4 3 3 5-6" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

// --- live results (auto-refreshes so the admin sees turnout update in real time) ---
async function loadResults() {
  const card = document.getElementById("results-card");
  const statRow = document.getElementById("stat-row");
  try {
    const data = await apiRequest("/api/admin/results");

    const turnoutPct = data.total_voters > 0
      ? Math.round((data.total_votes_cast / data.total_voters) * 100)
      : 0;

    statRow.innerHTML = `
      <div class="stat-box">
        <div class="stat-icon accent">${ICON_VOTERS}</div>
        <div><div class="stat-value">${data.total_voters}</div><div class="stat-label">Registered Voters</div></div>
      </div>
      <div class="stat-box">
        <div class="stat-icon deep">${ICON_VOTED}</div>
        <div><div class="stat-value">${data.total_votes_cast}</div><div class="stat-label">Votes Cast</div></div>
      </div>
      <div class="stat-box">
        <div class="stat-icon accent">${ICON_TURNOUT}</div>
        <div><div class="stat-value">${turnoutPct}%</div><div class="stat-label">Turnout</div></div>
      </div>`;

    if (data.portfolios.length === 0) {
      card.innerHTML = "<p class='subtitle'>No portfolios created yet.</p>";
      return;
    }

    card.innerHTML = "";
    data.portfolios.forEach((portfolio) => {
      const block = document.createElement("div");
      block.className = "portfolio-block";

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
          const isLeading = count > 0 && count === Math.max(portfolio.yes_votes, portfolio.no_votes) && portfolio.yes_votes !== portfolio.no_votes;
          const row = document.createElement("div");
          row.className = "bar-row";
          row.innerHTML = `
            <div class="bar-label"><span>${label} ${isLeading ? '<span class="leading-badge">Leading</span>' : ''}</span><span class="count">${count}</span></div>
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
      const voteCounts = portfolio.candidates.map((c) => c.votes);
      const isTie = voteCounts.filter((v) => v === maxVotes).length > 1;

      portfolio.candidates.forEach((candidate) => {
        const pct = Math.round((candidate.votes / maxVotes) * 100);
        const isLeading = candidate.votes > 0 && candidate.votes === maxVotes && !isTie;
        const row = document.createElement("div");
        row.className = "bar-row";
        row.innerHTML = `
          <div class="bar-label"><span>${candidate.name} ${isLeading ? '<span class="leading-badge">Leading</span>' : ''}</span><span class="count">${candidate.votes}</span></div>
          <div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div>`;
        block.appendChild(row);
      });

      card.appendChild(block);
    });
  } catch (err) {
    card.innerHTML = `<div class="msg error">${err.message}</div>`;
  }
}

loadResults();
setInterval(loadResults, 8000);
