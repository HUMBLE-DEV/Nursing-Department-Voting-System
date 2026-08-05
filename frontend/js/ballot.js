// Redirect to login if there's no token at all
if (!getToken()) window.location.href = "index.html";

const ballotView = document.getElementById("ballot-view");
const resultsView = document.getElementById("results-view");
const submitBtn = document.getElementById("submit-vote-btn");
const voteMsg = document.getElementById("vote-msg");
const closedBanner = document.getElementById("closed-banner");
const resultsToggle = document.getElementById("results-toggle");

const confirmModal = document.getElementById("confirm-modal");
const confirmList = document.getElementById("confirm-list");
const confirmCancel = document.getElementById("confirm-cancel");
const confirmSubmit = document.getElementById("confirm-submit");

// selections[portfolio_id] = { candidate_uid, is_yes }
// is_yes stays null for normal multi-candidate portfolios, and becomes
// true/false only for referendum (single-aspirant) portfolios.
let selections = {};
let portfolios = [];   // full ballot data, kept so we know every portfolio's title/candidates
let votingOpen = true;
let showingResults = false;

document.getElementById("logout-btn").addEventListener("click", () => {
  clearToken();
  window.location.href = "index.html";
});

resultsToggle.addEventListener("click", () => {
  showingResults = !showingResults;
  resultsToggle.textContent = showingResults ? "Back to Ballot" : "View Results";
  ballotView.classList.toggle("hidden", showingResults);
  submitBtn.classList.toggle("hidden", showingResults || !votingOpen);
  resultsView.classList.toggle("hidden", !showingResults);
  if (showingResults) loadResults();
});

async function loadBallot() {
  try {
    const data = await apiRequest("/api/student/ballot");
    votingOpen = data.voting_open;
    portfolios = data.ballot;

    if (!votingOpen) {
      closedBanner.classList.remove("hidden");
    }

    ballotView.innerHTML = "";
    portfolios.forEach((portfolio) => {
      const block = document.createElement("div");
      block.className = "portfolio-block";

      const title = document.createElement("div");
      title.className = "portfolio-title";
      title.textContent = portfolio.title;
      block.appendChild(title);

      const hint = document.createElement("div");
      hint.className = "portfolio-hint";
      hint.id = `hint-${portfolio.portfolio_id}`;
      hint.textContent = portfolio.is_referendum
        ? "Please answer Yes or No for this position."
        : "Please select a candidate for this position.";
      block.appendChild(hint);

      if (portfolio.is_referendum) {
        block.appendChild(renderReferendum(portfolio, hint));
      } else {
        block.appendChild(renderCandidateGrid(portfolio, hint));
      }

      ballotView.appendChild(block);
    });

    if (votingOpen) submitBtn.classList.remove("hidden");
  } catch (err) {
    ballotView.innerHTML = `<div class="msg error">${err.message}</div>`;
  }
}

// --- normal multi-candidate portfolio: grid of headshots, pick one ---
function renderCandidateGrid(portfolio, hint) {
  const grid = document.createElement("div");
  grid.className = "candidate-grid";

  portfolio.candidates.forEach((candidate) => {
    const card = document.createElement("div");
    card.className = "candidate-card";
    card.innerHTML = `
      <img class="candidate-photo" src="${candidate.photo_url || ''}" onerror="this.style.opacity=0">
      <div class="candidate-name">${candidate.name}</div>
      <div class="candidate-bio">${candidate.bio || ''}</div>
      <span class="candidate-check">Selected</span>`;
    card.addEventListener("click", () => {
      if (!votingOpen) return;
      selections[portfolio.portfolio_id] = { candidate_uid: candidate.uid, is_yes: null };
      hint.classList.remove("show");
      [...grid.children].forEach((el) => el.classList.remove("selected"));
      card.classList.add("selected");
    });
    grid.appendChild(card);
  });

  return grid;
}

// --- referendum portfolio: single aspirant shown with a Yes / No choice ---
function renderReferendum(portfolio, hint) {
  const wrap = document.createElement("div");
  const candidate = portfolio.candidates[0];

  const profile = document.createElement("div");
  profile.style.display = "flex";
  profile.style.alignItems = "center";
  profile.style.gap = "14px";
  profile.style.marginBottom = "14px";
  profile.innerHTML = `
    <img class="candidate-photo" style="width:64px;height:64px;margin-bottom:0;" src="${candidate.photo_url || ''}" onerror="this.style.opacity=0">
    <div>
      <div class="candidate-name">${candidate.name}</div>
      <div class="candidate-bio">${candidate.bio || ''}</div>
    </div>`;
  wrap.appendChild(profile);

  const choiceRow = document.createElement("div");
  choiceRow.style.display = "grid";
  choiceRow.style.gridTemplateColumns = "1fr 1fr";
  choiceRow.style.gap = "12px";

  [{ label: "Yes", value: true }, { label: "No", value: false }].forEach(({ label, value }) => {
    const card = document.createElement("div");
    card.className = "candidate-card";
    card.style.padding = "18px 8px";
    card.innerHTML = `<div class="candidate-name" style="font-size:16px;">${label}</div>`;
    card.addEventListener("click", () => {
      if (!votingOpen) return;
      selections[portfolio.portfolio_id] = { candidate_uid: candidate.uid, is_yes: value };
      hint.classList.remove("show");
      [...choiceRow.children].forEach((el) => el.classList.remove("selected"));
      card.classList.add("selected");
    });
    choiceRow.appendChild(card);
  });

  wrap.appendChild(choiceRow);
  return wrap;
}

// step 1: check every portfolio has a choice, then show the confirmation modal
submitBtn.addEventListener("click", () => {
  const missing = portfolios.filter((p) => !selections[p.portfolio_id]);

  if (missing.length > 0) {
    missing.forEach((p) => {
      document.getElementById(`hint-${p.portfolio_id}`).classList.add("show");
    });
    showMessage(
      voteMsg,
      `Please select an answer for: ${missing.map((p) => p.title).join(", ")}.`,
      "error"
    );
    document.getElementById(`hint-${missing[0].portfolio_id}`).scrollIntoView({ behavior: "smooth", block: "center" });
    return;
  }

  // build a readable summary for the confirmation dialog
  confirmList.innerHTML = portfolios.map((portfolio) => {
    const choice = selections[portfolio.portfolio_id];
    if (portfolio.is_referendum) {
      return `<li><strong>${portfolio.title}:</strong> ${choice.is_yes ? "Yes" : "No"}</li>`;
    }
    const candidate = portfolio.candidates.find((c) => c.uid === choice.candidate_uid);
    return `<li><strong>${portfolio.title}:</strong> ${candidate ? candidate.name : ""}</li>`;
  }).join("");

  confirmModal.classList.remove("hidden");
});

confirmCancel.addEventListener("click", () => {
  confirmModal.classList.add("hidden");
});

// step 2: only actually submits once the person confirms in the modal
confirmSubmit.addEventListener("click", async () => {
  confirmSubmit.disabled = true;
  confirmSubmit.textContent = "Submitting...";

  const choices = Object.entries(selections).map(([portfolio_id, choice]) => ({
    portfolio_id: Number(portfolio_id),
    candidate_uid: choice.candidate_uid,
    is_yes: choice.is_yes,
  }));

  try {
    const data = await apiRequest("/api/student/vote", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ choices }),
    });
    confirmModal.classList.add("hidden");
    showMessage(voteMsg, data.message, "success");
    submitBtn.disabled = true;
    submitBtn.textContent = "Vote Already Submitted";
  } catch (err) {
    confirmModal.classList.add("hidden");
    showMessage(voteMsg, err.message, "error");
  } finally {
    confirmSubmit.disabled = false;
    confirmSubmit.textContent = "Yes, Cast My Vote";
  }
});

// --- results: headshot row with live counts, then a bar chart per portfolio ---
async function loadResults() {
  resultsView.innerHTML = "<p class='subtitle'>Loading results...</p>";
  try {
    const data = await apiRequest("/api/student/results");
    resultsView.innerHTML = "";

    const statRow = document.createElement("div");
    statRow.className = "stat-row";
    statRow.innerHTML = statCardsHTML(data.total_voters, data.total_votes_cast);
    resultsView.appendChild(statRow);

    data.portfolios.forEach((portfolio) => {
      resultsView.appendChild(renderPortfolioResult(portfolio));
    });
  } catch (err) {
    resultsView.innerHTML = `<div class="msg error">${err.message}</div>`;
  }
}

function statCardsHTML(voters, votesCast) {
  return `
    <div class="stat-box">
      <div class="stat-icon accent">${ICON_VOTERS}</div>
      <div><div class="stat-value">${voters}</div><div class="stat-label">Registered Voters</div></div>
    </div>
    <div class="stat-box">
      <div class="stat-icon deep">${ICON_VOTED}</div>
      <div><div class="stat-value">${votesCast}</div><div class="stat-label">Votes Cast</div></div>
    </div>`;
}

function renderPortfolioResult(portfolio) {
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
      const row = document.createElement("div");
      row.className = "bar-row";
      row.innerHTML = `
        <div class="bar-label"><span>${label}</span><span class="count">${count}</span></div>
        <div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div>`;
      block.appendChild(row);
    });

    return block;
  }

  // headshot row with vote counts under each candidate, like a nominations-results view
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

  return block;
}

const ICON_VOTERS = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
const ICON_VOTED = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4" stroke-linecap="round" stroke-linejoin="round"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

loadBallot();
