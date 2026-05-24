# Deploy to Fly.io — step-by-step

> Goal: get `https://job-tracker-ajinkya.fly.dev` (or your chosen subdomain) live, protected by HTTP basic auth, accessible from your phone 24/7. ~20–30 min including CLI install.
>
> Codebase is already prepped: `Dockerfile`, `.dockerignore`, `fly.toml`, `Procfile`, `requirements.txt`. `webapp.py` reads config from env vars and refuses to start in production without auth (safety guard).

---

## What you'll need

- Your **GitHub login** (`AjinkyaKate`) — easiest sign-in for Fly
- A **payment method** to verify (Fly asks for one even on free tier; free allowance covers this app)
- A **strong password** for HTTP basic auth (write it down — you'll need it on phone too)
- ~20–30 min, with terminal access on your Mac

---

## Step 1 — Install the Fly CLI (`flyctl`)

In your terminal on the Mac:

```bash
brew install flyctl
```

If you don't have Homebrew, use the curl installer instead:

```bash
curl -L https://fly.io/install.sh | sh
```

Verify it's installed:

```bash
flyctl version
```

You should see something like `flyctl v0.x.xxx`.

---

## Step 2 — Sign up + log in

```bash
flyctl auth signup    # opens browser. Sign in with GitHub.
```

If you already have a Fly account:

```bash
flyctl auth login
```

Fly will ask for a payment method during signup. Your usage is well below the free allowance (~$0/month), but the verification step is mandatory.

---

## Step 3 — Pick a globally-unique app name

Fly app names are globally unique (like usernames). Edit `fly.toml` and change the `app` line if `job-tracker-ajinkya` is taken:

```toml
app = "job-tracker-ajinkya"   # change this if Fly says it's taken
```

Then create the app:

```bash
cd "/Users/ajinkya/Desktop/Ajinkya Kate/job-tracker"
flyctl apps create job-tracker-ajinkya   # use the same name as fly.toml
```

If you get `name not available`, pick a new one (e.g. `ajinkya-job-tracker-2026`), update `fly.toml`, and re-run.

Once created, the URL will be `https://<your-app-name>.fly.dev`. Write this down — you'll need it in Step 5 and Step 7.

---

## Step 4 — Create the persistent volume

This is what keeps your `tracker.db` alive between deploys.

```bash
flyctl volumes create tracker_data --size 1 --region bom -a job-tracker-ajinkya
```

(Replace `job-tracker-ajinkya` with your actual app name everywhere below.)

It asks "Do you really want to use single-node SSD?" — answer **yes**. Single-node is correct for a single-user app with SQLite.

---

## Step 5 — Set your secrets

These become env vars inside the running container. **Run this in one command** so Fly batches the deploy.

```bash
flyctl secrets set \
  ADMIN_USERNAME="ajinkya" \
  ADMIN_PASSWORD="<pick-a-strong-password>" \
  GOOGLE_CLIENT_ID="783422059264-0aof78coba8cipi11mluoa6288btf4do.apps.googleusercontent.com" \
  GOOGLE_CLIENT_SECRET="<paste-your-GOCSPX-secret>" \
  GOOGLE_REDIRECT_URI="https://job-tracker-ajinkya.fly.dev/auth/gmail/callback" \
  -a job-tracker-ajinkya
```

Replace:
- `<pick-a-strong-password>` with a long random password (save it in a password manager — you'll type it on phone too)
- `<paste-your-GOCSPX-secret>` with your Google OAuth Client Secret from `.env`
- The redirect URI domain to match your actual app name

> Fly does NOT print secret values back. They're encrypted at rest. You can re-set any of them later with the same command.

---

## Step 6 — Update Google Cloud Console

The Gmail OAuth callback URL changed (from `localhost:8000` to your Fly subdomain). You need to whitelist the new URL in Google Cloud Console, or Gmail auth will fail.

1. Open **https://console.cloud.google.com/apis/credentials**
2. Click your OAuth 2.0 Client ID (the one for `783422059264-...`)
3. Under **Authorized redirect URIs**, click **+ ADD URI** and add:
   ```
   https://job-tracker-ajinkya.fly.dev/auth/gmail/callback
   ```
4. Click **Save**
5. Leave the localhost URI in place too — handy for local dev later.

---

## Step 7 — Deploy

```bash
flyctl deploy -a job-tracker-ajinkya
```

This builds the Docker image, pushes it, starts the machine, mounts the volume, runs the schema migration. Takes ~2–3 min the first time.

**Watch the log** — if anything fails, it prints why. Common issues are in Troubleshooting below.

When it says `deployed successfully`, the URL is live. Visit:

```
https://job-tracker-ajinkya.fly.dev
```

You'll get a browser HTTP-basic-auth prompt. Enter `ADMIN_USERNAME` + `ADMIN_PASSWORD` from Step 5. The dashboard loads — **empty**, because we haven't uploaded your local tracker.db yet. That's Step 8.

---

## Step 8 — Migrate your local tracker.db to the Fly volume

Your Mac's `tracker.db` has 30 real jobs. Upload it.

First, **make a local backup** (in case something goes sideways):

```bash
cp tracker.db tracker.db.backup-$(date +%Y%m%d)
```

Then SSH into the Fly machine and check what's there:

```bash
flyctl ssh console -a job-tracker-ajinkya
# inside container:
ls -la /data
exit
```

You should see an empty `tracker.db` Fly created when the app first started. Now upload your real DB on top of it via SFTP:

```bash
flyctl ssh sftp shell -a job-tracker-ajinkya
# inside sftp:
put tracker.db /data/tracker.db
exit
```

Restart the app so it picks up the new DB cleanly:

```bash
flyctl apps restart job-tracker-ajinkya
```

Reload the URL in your browser. You should now see all 30 jobs.

---

## Step 9 — Verify from phone

1. Open the same `https://job-tracker-ajinkya.fly.dev` on your phone
2. Browser prompts for username/password → enter the same ones
3. You should see the full kanban + all 30 jobs
4. Drag a card to a new column from desktop → refresh phone → status updated
5. Tap a card on phone → use the new "Move to ..." status buttons → returns to dashboard with card in new column

**You're deployed. Running 24/7.**

---

## Step 10 — Test Gmail sync end-to-end

1. On phone or desktop, click the **"Connect Gmail"** button on the dashboard
2. Should redirect to Google's consent screen
3. Pick your Gmail account, grant `gmail.readonly`
4. Redirects back to your dashboard. The Gmail widget should now say "Connected".
5. Click **"Sync Now"**. Wait ~10s. New events from LinkedIn emails appear under each job's activity feed.

If you get an OAuth error: the redirect URI in Google Cloud Console doesn't match `GOOGLE_REDIRECT_URI` in Fly secrets. Both must be the exact same string including trailing path.

---

## Daily ops

| Action | Command |
|---|---|
| View live logs | `flyctl logs -a job-tracker-ajinkya` |
| SSH into container | `flyctl ssh console -a job-tracker-ajinkya` |
| Download a backup of prod DB | `flyctl ssh sftp shell -a job-tracker-ajinkya` → `get /data/tracker.db ./prod-backup.db` |
| Update a secret | `flyctl secrets set KEY=value -a job-tracker-ajinkya` |
| Deploy a new version | push to GitHub + `flyctl deploy -a job-tracker-ajinkya` (or wire up auto-deploy later) |
| Restart the app | `flyctl apps restart job-tracker-ajinkya` |
| See app status | `flyctl status -a job-tracker-ajinkya` |
| Stop billing entirely | `flyctl apps destroy job-tracker-ajinkya` (irreversible) |

---

## Troubleshooting

- **`flyctl apps create` says name not available** → pick another, update `fly.toml`'s `app =` line to match.
- **Build fails with "Detected production deploy but ADMIN_USERNAME or ADMIN_PASSWORD env var is missing"** → you skipped Step 5. Run the `flyctl secrets set` command.
- **App starts but the URL returns 502** → uvicorn isn't binding to `$PORT`. Check `Dockerfile`'s CMD line wasn't edited; should use `${PORT:-8080}`.
- **Auth prompt keeps appearing** → wrong username/password. Reset with `flyctl secrets set ADMIN_PASSWORD=...`.
- **Page loads but is empty after Step 8** → DB upload didn't land. SSH in (`flyctl ssh console`), `ls -la /data`, confirm `tracker.db` size matches your local file. If it's still small, re-upload via SFTP.
- **Gmail OAuth `redirect_uri_mismatch`** → the URL in Google Cloud Console doesn't exactly match the `GOOGLE_REDIRECT_URI` secret. Compare both character-by-character (https vs http, trailing slash, etc.).
- **Page hangs after Fly says deployed** → first request after restart can be slow as Python boots. Wait 5–10s and retry.

Paste any error log into chat and I'll diagnose.

---

## Cost expectations

This single-machine app on `shared-cpu-1x@256MB` + 1GB volume runs at **$0/month** as long as you stay within Fly's free allowance:

- 3 shared-cpu-1x VMs free (we use 1)
- 3 GB persistent volume free (we use 1)
- 160 GB outbound bandwidth free (we use ~negligible)

If you ever scale up or add more apps, Fly charges per resource. Monitor at `flyctl dashboard`.
