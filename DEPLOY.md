# Deploy to Render (free tier, no credit card) — step-by-step

> Goal: `https://job-tracker.onrender.com` (or similar) live 24/7, protected by HTTP basic auth, accessible from anywhere on any device. ~20 min including signup.
>
> Architecture: FastAPI web service + Render-managed PostgreSQL. SQLite (local dev) and Postgres (prod) are both supported by the same codebase via `db.py`, selected by the `DATABASE_URL` env var.

---

## Free-tier reality check

Render's free tier has two things you should know about before starting:

1. **Web service sleeps after 15 min idle.** First request after sleep takes ~30 seconds to wake. Once awake, it stays warm for 15 min after each request.
2. **Free Postgres expires after 90 days of inactivity.** Using the tracker daily keeps it alive indefinitely. If you stop using it for 3 months, the DB is deleted.

Neither is a deal-breaker for a personal job tracker that you check multiple times a day.

---

## Step 1 — Sign up at render.com

Open **https://render.com/register** in your browser. Pick **"Sign up with GitHub"** (same `AjinkyaKate` login). Authorize Render to read your repos. You're now on the Render dashboard.

**No credit card required.**

---

## Step 2 — Create the Blueprint

A Blueprint reads `render.yaml` in your repo and provisions everything in one click.

1. Top-right of the dashboard, click **"New +"** → **"Blueprint"**
2. **"Connect a repository"** → pick `AjinkyaKate/job-tracker`
3. Render reads `render.yaml` and shows a preview: 1 web service (`job-tracker`) + 1 PostgreSQL database (`job-tracker-db`)
4. Click **"Apply"**

Render starts building the web service AND provisioning the database in parallel. The build will likely fail the first time with "Detected production deploy but ADMIN_USERNAME or ADMIN_PASSWORD env var is missing" — that's the safety guard. We fix that in Step 4.

---

## Step 3 — Wait for Postgres to be ready (~1 min)

In the dashboard, click on the database service (`job-tracker-db`). Status should change to **"Available"** within ~60 seconds. Note the **Internal Database URL** — looks like `postgresql://job_tracker_user:xxxx@dpg-xxxxx-a/job_tracker_db_xxxx`. This is what `DATABASE_URL` will resolve to inside the web service.

You don't need to copy it — `render.yaml` auto-wires it to the web service.

---

## Step 4 — Set your secret env vars on the web service

In the dashboard, click on the web service (`job-tracker`). Open the **Environment** tab.

You'll see 5 env vars with **"Required"** badges that need values:

| Key | Value |
|---|---|
| `ADMIN_USERNAME` | `ajinkya` (or whatever you want) |
| `ADMIN_PASSWORD` | A strong password. **Save it in your password manager.** |
| `GOOGLE_CLIENT_ID` | `<YOUR_CLIENT_ID>.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Paste your `GOCSPX-...` from local `.env` |
| `GOOGLE_REDIRECT_URI` | `https://job-tracker.onrender.com/auth/gmail/callback` (use your actual Render URL once Step 5 confirms it) |

Click **"Save Changes"**. Render auto-redeploys.

---

## Step 5 — Wait for the redeploy

Watch the **Events** tab. The redeploy should finish in ~2 minutes (Render free-tier builds are slower than paid). Status: **Live** (green dot).

If it fails again, paste the log into chat and I'll diagnose.

Once live, your URL is shown on the service overview: `https://job-tracker.onrender.com` (or `job-tracker-xxxx.onrender.com` if `job-tracker` was taken).

---

## Step 6 — First visit + auth prompt

1. Open the URL in your browser
2. Browser prompts for HTTP basic auth → enter `ADMIN_USERNAME` + `ADMIN_PASSWORD`
3. You'll see the dashboard. **Empty** — Postgres is fresh. We sync data in Step 7.

---

## Step 7 — Migrate your local data to Render Postgres

Your Mac has 31 jobs in `tracker.db`. We push them to Render's Postgres.

First, **make a local backup** in case anything goes sideways:

```bash
cp tracker.db tracker.db.backup-$(date +%Y%m%d)
```

Then get the **External Database URL** from Render (different from the Internal one — the External one is reachable from your laptop):

1. In Render dashboard → `job-tracker-db` → **Info** tab
2. Copy the **External Database URL** (looks like `postgresql://job_tracker_user:xxxx@dpg-xxxxx-a.singapore-postgres.render.com/job_tracker_db_xxxx`)
3. Run the migration locally, pointing at that URL:

```bash
cd "/Users/ajinkya/Desktop/Ajinkya Kate/job-tracker"
.venv/bin/python migrate_to_postgres.py \
  --source tracker.db \
  --target "<paste-external-database-url-here>"
```

You'll see:

```
✓ Target schema ensured
Copying tables:
  jobs                   src=31 -> inserted=31
  contacts               src=18 -> inserted=18
  events                 src=N  -> inserted=N
  ...
Resetting sequences:
  jobs                   sequence jobs_id_seq -> 31
  ...
Verifying row counts:
  [OK ] jobs                   source=31 target=31
  [OK ] contacts               source=18 target=18
  ...
✓ Migration complete. All row counts match.
```

If any count mismatches, the script exits with code 3 and details. Paste output into chat and I'll diagnose.

---

## Step 8 — Reload the public URL

Refresh `https://job-tracker.onrender.com` in your browser. All 31 jobs visible in the kanban.

---

## Step 9 — Verify from phone

1. Open the same URL on your phone (mobile data, *not* WiFi — proves it's reachable from the open internet)
2. Browser prompts auth → enter the same credentials
3. You should see the dashboard with all jobs
4. Tap a card → use the "Move to ..." status buttons → returns to dashboard with card in new column

**You're deployed. Running 24/7.** Modulo the 15-min idle sleep — first request after a long pause will be ~30 sec slow, then normal.

---

## Step 10 — Update Google Cloud Console for Gmail OAuth

The Gmail callback URL is now your Render domain, not localhost. Add it to Google Cloud Console's authorized redirects:

1. Open **https://console.cloud.google.com/apis/credentials**
2. Click your OAuth 2.0 Client ID
3. Under **Authorized redirect URIs**, click **"+ ADD URI"** and add:
   ```
   https://job-tracker.onrender.com/auth/gmail/callback
   ```
   (use your actual Render URL)
4. Click **Save**
5. Keep the `http://localhost:8000/auth/gmail/callback` entry too — handy for local dev.

Then on the deployed app, click **"Connect Gmail"** → Google consent → back to dashboard → **"Sync Now"**. Should pull recent LinkedIn emails.

---

## Daily ops

| Action | How |
|---|---|
| View live logs | Render dashboard → web service → **Logs** tab |
| Run a Postgres query | Render dashboard → database → **Connect** → "PSQL Command" |
| Update a secret | Render dashboard → web service → **Environment** → edit value → save (auto-redeploys) |
| Deploy a new version | `git push` to main; Render auto-deploys |
| Restart the app | Dashboard → **Manual Deploy** → "Clear build cache & deploy" |
| Backup the DB | Dashboard → database → **Backups** (free tier: 1 backup, no automatic) |
| Download local backup | `pg_dump "<external-url>" > backup.sql` from your Mac |

---

## Troubleshooting

- **Build fails: "ADMIN_USERNAME missing"** → set the 5 env vars in Step 4.
- **Build fails: Python version error** → confirm `.python-version` says `3.11`. Render respects it.
- **App live but URL returns 502** → uvicorn isn't binding to `$PORT`. Check `render.yaml`'s `startCommand`.
- **Auth prompt keeps appearing** → wrong username/password. Reset via Environment tab.
- **App page loads but blank dashboard** → `DATABASE_URL` wired but tables not created. Hit the URL once (visiting `/` triggers `tracker.init_db()` which creates tables). Then migrate data again.
- **Migration script: "could not connect to server"** → using Internal URL instead of External. Internal URL only works from inside Render's network.
- **Gmail OAuth: `redirect_uri_mismatch`** → the URL in Google Cloud Console doesn't exactly match `GOOGLE_REDIRECT_URI`. Compare char-by-char.
- **App is slow on first request** → expected. Free tier sleeps after 15 min idle.

---

## Cost expectations

Render free tier:
- Web service: 750 hrs/month free (24/7 = 720 hrs, fits inside)
- PostgreSQL free tier: 1 GB storage, 256 MB RAM, expires after 90 days idle
- 100 GB bandwidth/month free

Real monthly bill: **$0**. If you ever want to upgrade (no sleep, persistent DB), Starter web service is $7/mo + Postgres is $7/mo.

---

## Why we migrated from SQLite to Postgres

The Render free tier has no persistent disk on the web service — every restart wipes the filesystem. SQLite needs a persistent file. So we use Render's managed PostgreSQL (which IS persistent) as the database, and the same Python codebase talks to either backend via `db.py`'s adapter.

Locally, you still use SQLite (`tracker.db`) — fast, no setup, works offline. The adapter checks for `DATABASE_URL` and switches backends automatically.
