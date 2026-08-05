# Nursing Department Voting System

A secure web-based voting app for a university department election. Students log in with their index number, verify with an emailed one-time code, then vote once per portfolio. Admins upload the approved student roster, create portfolios and candidates (with photos and bios), and watch results update live.

**Stack:** FastAPI (async) + SQLite + plain HTML/JS frontend, all served from one process.

---

## 1. Before you touch any code

Set the real election close date/time. This is the one setting that matters most — get it wrong and voting either never locks or locks immediately.

Open `app/config.py` and edit:

```python

```

Change the year, month, day, hour, minute to your actual election close time.

---

## 2. Running it locally

```bash
# 1. Create a virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install uv
init uv
uv add -r requirements.txt

# 3. Copy the env file and fill it in
cp .env.example .env
```

Open `.env` and set at minimum:
- `JWT_SECRET_KEY` — any long random string (e.g. generate one with `python3 -c "import secrets; print(secrets.token_hex(32))"`)
- `FIRST_ADMIN_INDEX`, `FIRST_ADMIN_PASSWORD`, `FIRST_ADMIN_EMAIL` — your own admin login
- SMTP settings (see section 5) — or leave blank to use dev mode (OTP codes print to the terminal instead of emailing)

```bash
# 4. Run the server
uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000` in your browser. That's the login/register page.

---

## 3. First-time admin setup

The first time the app starts, it automatically creates one admin account using the `FIRST_ADMIN_*` values from your `.env`. Log in with those to reach the admin dashboard.

**Do these three things before voting opens, in order:**

1. **Upload the roster.** Prepare a CSV with two columns:
   ```
   level,index_number
   300,UENR/CS/21/0045
   300,UENR/CS/21/0046
   200,UENR/CS/22/0012
   ```
   Upload it on the admin dashboard under "Upload Approved Roster". This is what students are checked against when they register — nobody can register with an index number that isn't in this file.

2. **Create portfolios** (e.g. President, Secretary, Treasurer) — one at a time, under "Create Portfolio".

3. **Add candidates** for each portfolio — name, a short bio, and optionally a photo. These are what students see on their ballot.

Students can now register and vote at the same URL.

---

## 4. How the login flow works

1. Student registers with level + index number + email + password. This only succeeds if that exact (level, index_number) pair is in the roster you uploaded.
2. Student logs in with index number + password.
3. If correct, a 6-digit code is emailed to them (or printed to your terminal in dev mode).
4. Student enters the code to receive their session — only then can they see the ballot or results.

This email step is a real security gate, not just decoration: even a correct password alone won't get anyone into the ballot.

---

## 5. Setting up real email (SMTP)

Without this, OTP codes just print to your terminal — fine for testing, not for a real election.

**Easiest option: Gmail with an App Password**

1. Go to your Google Account → Security → turn on 2-Step Verification (required first).
2. Go to Security → App Passwords → generate one for "Mail".
3. Put these in `.env`:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=the-16-character-app-password
   ```

Do **not** use your normal Gmail password — it won't work and Google will block it.

---

## 6. Deploying to Render

1. Push this project to a GitHub repo.
2. On Render, create a new **Web Service**, connect the repo.
3. Render will detect the `Dockerfile` automatically — no build command needed.
4. Add every variable from `.env.example` under Render's **Environment** tab (not as a file — Render's dashboard, one by one).
5. **Add a persistent disk** (Render dashboard → your service → Disks → Add Disk, ~1GB, mounted at `/app`). Without this, your SQLite database gets wiped every time the service restarts or redeploys — this step is not optional for a real election.
6. Deploy. Your first admin account is created automatically on first startup, same as local.

---

## 7. Project structure

```
app/
├── main.py            # entrypoint — wires everything together
├── config.py          # settings, including ELECTION_CLOSE
├── database.py        # SQLite engine + session setup
├── models/            # database tables (Voter, ApprovedRoster, Portfolio, Candidate, Vote)
├── schemas/            # request/response shapes
├── core/               # password hashing, JWT, auth dependency
├── services/           # business logic: roster check, election clock, OTP email, results
├── routers/             # the actual API endpoints (auth, admin, student)
└── seed.py             # creates the first admin account on startup

frontend/
├── index.html          # login / register
├── admin.html          # admin dashboard
├── ballot.html         # student ballot + live results
└── js/ css/             # supporting logic and styling
```

---

## 8. If something breaks on election day

- **"Voting has closed" but it shouldn't be** → check `ELECTION_CLOSE` in `app/config.py` matches the real close time and timezone.
- **A student says they never got an OTP email** → check your SMTP settings are correct in Render's environment variables, and check your email provider's sent folder / spam reports. As a fallback, you (the admin) can look at server logs for `[DEV MODE]` lines if SMTP isn't configured.
- **"Index number not found for this level"** → the student either mistyped it, or it's missing from the roster CSV. Add it via another roster upload (duplicates are skipped safely).
- **Results look wrong** → results are always computed live from the vote table, never cached, so a page refresh should always be accurate.
