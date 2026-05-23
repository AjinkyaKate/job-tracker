# Deploy to Railway — step-by-step

> Goal: get `https://job-tracker.up.railway.app` (or similar) live, protected by HTTP basic auth, accessible from your phone. ~10–15 min of clicks.
>
> The codebase is already prepped: `Procfile` tells Railway how to start; `requirements.txt` lists deps; `webapp.py` reads config from env vars and refuses to start in production without auth (safety guard).

---

## What you'll need

- Your **GitHub login** (`AjinkyaKate`) — easiest sign-in for Railway
- A **strong password** for the deployed app's HTTP basic auth (write it down — you'll need it on phone)
- ~10–15 min

---

## Step 1 — Sign up at railway.app

1. Open **https://railway.app** in your browser
2. Click **Sign up** (or **Log in** if you already have one)
3. Pick **"Continue with GitHub"** — authorize Railway to read your repo
4. You'll land on your Railway dashboard. New users get a free $5/month credit — covers personal use for months.

---

## Step 2 — Create the project from the GitHub repo

1. Click **"New Project"** (top right)
2. Pick **"Deploy from GitHub repo"**
3. Authorize Railway to access `AjinkyaKate/job-tracker` (you may need to grant access in GitHub for this specific repo if it's private)
4. Pick the repo. Railway detects Python from `requirements.txt` and starts the first build.

**Wait ~2 min** for the first build. It will likely **fail** with an error like *"Detected production deploy but ADMIN_USERNAME or ADMIN_PASSWORD env var is missing."* That's the safety guard working — it's protecting you from accidentally exposing personal data. Move to Step 3.

---

## Step 3 — Add a persistent volume (so your data survives deploys)

Railway containers are stateless by default. Without a volume, every deploy = empty `tracker.db`. We mount a volume to persist it.

1. In your Railway project, click on the service (it'll be named `job-tracker`)
2. Click **Settings** → scroll to **Volumes**
3. Click **"+ New Volume"**
4. Mount path: **`/data`**
5. Click create. Railway provisions a small persistent disk.

---

## Step 4 — Set 3 environment variables

1. Still in your service, click **Variables** (top tab)
2. Click **"+ New Variable"** and add these three:

| Name | Value | Notes |
|---|---|---|
| `DB_FILE` | `/data/tracker.db` | Tells the app to use the volume, not the ephemeral filesystem |
| `ADMIN_USERNAME` | `ajinkya` *(or anything)* | What you'll type when prompted |
| `ADMIN_PASSWORD` | *a strong password* | What you'll type when prompted. **Save this in a password manager — you'll need it on phone too.** |

Click save. Railway will auto-redeploy.

---

## Step 5 — Wait for the redeploy

1. Click **Deployments** to watch it build
2. Should complete in 1–2 min. Status: **Active** (green)
3. If it still fails, the build logs tell you why. Paste the error in our chat and I'll fix it.

---

## Step 6 — Get the URL + visit

1. Back on your service overview, click **Settings** → **Networking** → **Generate Domain**
2. Railway gives you a URL like `job-tracker-production-xxxx.up.railway.app`
3. Click it (or paste in browser)
4. You'll get a **browser HTTP-basic-auth prompt**: enter your `ADMIN_USERNAME` + `ADMIN_PASSWORD`
5. You should see the dashboard. **It will be empty** (no jobs yet) — your local `tracker.db` hasn't been uploaded. That's expected. We sync data in the next step.

---

## Step 7 — Verify from phone

1. On your phone, open the same URL
2. Browser will prompt for username/password — enter the same ones
3. You should see the same empty dashboard
4. 🎉 **You're deployed.** Tell me in chat: "deployed, URL is ..."

---

## Step 8 — (next turn) Sync your local data to production

Once we know the deploy is alive, we sync your 16 jobs + contacts + events from your Mac's `tracker.db` up to Railway's volume. Two options for next turn:

- **Option A — Railway CLI:** install `railway` command on your Mac, run a one-shot copy
- **Option B — Upload endpoint:** I add a temporary `/admin/upload-db` POST endpoint, you `curl` your DB file up, I remove the endpoint after

Either gets your data live within ~5 min after deploy is confirmed.

---

## Troubleshooting

- **Build fails with "ADMIN_USERNAME missing"** → you skipped Step 4. Set the env vars in **Variables** tab.
- **Build fails with Python version error** → check `.python-version` says `3.11`. Railway should respect it.
- **App starts but URL returns 502** → the app is starting but not binding to `$PORT`. Check Procfile is committed.
- **Auth prompt loops forever** → wrong username/password. Reset in **Variables**.
- **Page renders but no data** → expected on first deploy. We sync data in Step 8.

When stuck, paste the Railway build/deploy logs into chat and I'll diagnose.
