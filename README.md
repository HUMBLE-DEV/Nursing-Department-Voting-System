# School Of Nursing Department Voting System


A secure web-based voting app for a university department election. Students log in with their index number, verify with an emailed one-time code, then vote once per portfolio — either picking a candidate, or answering Yes/No for uncontested (single-aspirant) positions. Admins upload the approved student roster, set the voting window, manage portfolios and candidates (with photos and bios), and watch results update live on their own dedicated results page.

**Stack:** FastAPI (async) + SQLite + plain HTML/JS frontend, all served from one process. No Docker Compose, no separate database service — one `Dockerfile`, one app, one file for the database.

---

## 1. Running it locally

```bash
# 1. Create a virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

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

## 2. First-time admin setup

The first time the app starts, it automatically creates one admin account using the `FIRST_ADMIN_*` values from your `.env`. Log in with those to reach the admin dashboard.

**Do these in order, before voting opens:**

1. **Set the election timing.** On the admin dashboard, under "Election Timing," set an Opens At and Closes At date/time (Ghana local time — the app converts this automatically). Leaving Closes At blank means voting never locks on its own, so don't forget this step before the real election.

2. **Upload the roster.** Prepare a CSV with two columns:
   ```
   level,index_number
   300,UENR/CS/21/0045
   300,UENR/CS/21/0046
   200,UENR/CS/22/0012
   ```
   This is what students are checked against when they register — nobody can register with an index number that isn't in this file.

3. **Create portfolios** (e.g. President, Secretary, Treasurer).

4. **Add candidates** for each portfolio — name, a short bio, and optionally a photo. **A portfolio with exactly one candidate automatically becomes a Yes/No vote** for students — no separate setting needed, it's based purely on candidate count.

Students can now register and vote at the same URL.

Portfolios can also be **deleted** from the dashboard if added by mistake — this removes any candidates and votes attached to it too, so use it with care once voting has actually started.

---

## 3. How the login flow works

1. Student registers with level + index number + email + password. This only succeeds if that exact (level, index_number) pair is in the roster you uploaded.
2. Student logs in with index number + password.
3. If correct, a 6-digit code is emailed to them (or printed to your terminal in dev mode) — sent as a background task, so the page responds instantly even if the email itself is slow to send.
4. Student enters the code to receive their session — only then can they see the ballot or results.

**Forgot password:** a student can reset their password from the login page's "Forgot password?" link. They must provide both their index number *and* their registered email — both have to match, or nothing is sent, and the response message is identical either way so the endpoint can't be used to check who's registered. A matching request sends a one-time reset code (same OTP mechanism as login) to their email.

---

## 4. Setting up real email (SMTP)

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

**If emails fail to send** (connection errors, timeouts): this no longer blocks or crashes anything — emails send in the background, and a failure is logged to your server console along with the OTP code as a fallback, so you (or the student) are never fully locked out. Common causes of a failed send: wrong `SMTP_HOST`/`SMTP_PORT`, using your regular Gmail password instead of an App Password, or your network/firewall blocking outbound port 587 (some campus/public WiFi and antivirus software do this — test from a different network if it keeps failing).

---

## 5. Deploying to Render

1. Push this project to a GitHub repo.
2. On Render, create a new **Web Service**, connect the repo.
3. Render will detect the `Dockerfile` automatically — no build command needed.
4. Add every variable from `.env.example` under Render's **Environment** tab (not as a file — Render's dashboard, one by one).
5. **Add a persistent disk** (Render dashboard → your service → Disks → Add Disk, ~1GB, mounted at `/app`). Without this, your SQLite database gets wiped every time the service restarts or redeploys — this step is not optional for a real election.
6. **Upgrade to the Starter plan (~$7/month)** for election day. Render's free tier spins the app down after 15 minutes of no traffic, causing a ~30-50 second delay on the next visitor — bad if that happens right as voting opens and many students hit the site at once. You can downgrade back to free right after the election closes.
7. Deploy. Your first admin account is created automatically on first startup, same as local.
8. **Before going live:** tighten CORS in `app/main.py` — change `allow_origins=["*"]` to your actual Render URL only.

---

## 6. Project structure

```
app/
├── main.py                  # entrypoint — wires everything together
├── config.py                # settings (secrets, SMTP, DB path)
├── database.py               # SQLite engine + session setup (WAL mode enabled)
├── models/                   # database tables: Voter, ApprovedRoster, Portfolio,
│                              # Candidate, Vote, ElectionSettings
├── schemas/                  # request/response shapes
├── core/                     # password hashing, JWT, auth dependency
├── services/                 # business logic: roster check, election clock
│                              # (admin-controlled timing), OTP email, results
├── routers/                  # the actual API endpoints (auth, admin, student)
└── seed.py                   # creates the first admin account on startup

frontend/
├── index.html                # login / register
├── forgot-password.html      # password reset flow
├── admin.html                # admin dashboard: timing, roster, portfolios, candidates
├── admin-results.html        # admin's live results page (separate from the dashboard)
├── ballot.html                # student ballot + live results
├── favicon.svg                 # browser tab icon
└── js/ css/                   # supporting logic and styling
```

---

## 7. About favicon.svg

`frontend/favicon.svg` is the small icon shown in the browser tab (and in bookmarks) — a blue ballot-box icon matching the app's color theme. It's linked in the `<head>` of every page:
```html
<link rel="icon" type="image/svg+xml" href="favicon.svg">
```
It's purely cosmetic — has no effect on functionality — but it's what makes the browser tab show your app's own icon instead of a blank page icon, and helps students recognize the right tab if they have several open. You can replace it with your own logo by swapping the file's contents, or by pointing that `<link>` tag at a different image (e.g. a `.png` version of your department's actual logo, if you have one).

---

## 8. If something breaks on election day

- **"Voting has closed" but it shouldn't be** → check the Opens At / Closes At values on the admin dashboard's Election Timing section.
- **A student says they never got an OTP email** → check your SMTP settings in Render's environment variables, and check your server logs for `[EMAIL SEND FAILED]` — the fallback OTP code is printed right there so you can read it out to the student directly if needed.
- **"Index number not found for this level"** → the student either mistyped it, or it's missing from the roster CSV. Add it via another roster upload (duplicates are skipped safely).
- **Results look wrong** → results are always computed live from the vote table, never cached, so a page refresh should always be accurate. The admin's results page additionally shows turnout % and a "Leading" badge, which students don't see on their own results view.
- **Student forgot their password** → they can use "Forgot password?" on the login page. If their email is also unreachable/wrong, you'll need to check their registered email in the database directly (see the SQLite section in earlier project notes, or ask if you need a refresher).
