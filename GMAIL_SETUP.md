# Gmail Integration Setup — Google Cloud Console

> Goal: get OAuth credentials so the Job Tracker can read your Gmail (specifically: LinkedIn notification emails) and auto-detect connection accepts, message replies, application updates etc.
>
> Scope requested: **`gmail.readonly`** — we only READ your emails, never send/delete/modify. You can revoke access anytime at [myaccount.google.com → Security → Third-party apps with account access](https://myaccount.google.com/permissions).
>
> Time: ~10 min of clicks in Google Cloud Console. All free tier.

---

## Why this exists

LinkedIn doesn't have a usable API for "did Krunal accept my request" or "did Latika reply." But LinkedIn **emails** you about every event — connection accepted, message received, InMail, application update, etc. By reading those Gmail messages (with your permission), the tracker auto-logs activity to the right job, no manual paste needed.

We use Google's official Gmail API — safe, sanctioned, doesn't touch LinkedIn TOS, doesn't risk your LinkedIn account.

---

## Step 1 — Create a Google Cloud project

1. Open **https://console.cloud.google.com/** (sign in with `<your-gmail@example.com>`)
2. At the top, click the project dropdown → **"New Project"**
3. Project name: **"job-tracker"** (or anything). Skip the "Organization" field. Click **Create**.
4. Wait ~10 seconds. Make sure the new project is **selected** in the top dropdown.

---

## Step 2 — Enable the Gmail API for this project

1. Left sidebar (☰) → **APIs & Services → Library**
2. Search for **"Gmail API"**
3. Click it → click **Enable**. Wait for confirmation.

---

## Step 3 — Configure the OAuth consent screen

1. Left sidebar → **APIs & Services → OAuth consent screen**
2. Pick **External** (you're not in a Google Workspace org). Click **Create**.
3. Fill in:
   - **App name:** `Job Tracker (personal)`
   - **User support email:** `<your-gmail@example.com>`
   - **Developer contact email:** `<your-gmail@example.com>`
   - Leave logo + domain fields blank.
4. Click **Save and Continue**.
5. **Scopes:** click **Add or Remove Scopes** → in the table, find and tick **`.../auth/gmail.readonly`** (search "gmail" if needed). Click **Update**, then **Save and Continue**.
6. **Test users:** click **+ Add Users** → enter `<your-gmail@example.com>` → click Add → Save and Continue. (This means only you can use this app while it's in "Testing" status — fine for personal use forever.)
7. Final screen → click **Back to Dashboard**.

---

## Step 4 — Create OAuth Client ID credentials

1. Left sidebar → **APIs & Services → Credentials**
2. Click **+ Create Credentials → OAuth client ID**
3. **Application type:** **Web application**
4. **Name:** `Job Tracker Web Client`
5. **Authorized redirect URIs:** click **+ Add URI** and add **exactly**:
   ```
   http://localhost:8000/auth/gmail/callback
   ```
   (Later when we deploy, we'll add the production URL too — e.g. `https://your-app.up.railway.app/auth/gmail/callback`. For now, localhost is enough.)
6. Click **Create**.
7. A modal appears with your **Client ID** and **Client secret**. **Copy both** — you'll paste them into `.env` in the next step. Also click **Download JSON** as a backup (save it somewhere private — it's your secret).

---

## Step 5 — Put credentials in `.env`

In the project folder (`~/Desktop/Ajinkya Kate/job-tracker`), create a file called `.env` (if it doesn't already exist) and add:

```
GOOGLE_CLIENT_ID=<paste your client ID here>
GOOGLE_CLIENT_SECRET=<paste your client secret here>
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/gmail/callback
```

`.env` is already in `.gitignore` from Ship 0 — these secrets never leave your machine.

---

## Step 6 — Confirm credentials are picked up

In your Cursor terminal (with `.venv` active):

```
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Client ID:', os.getenv('GOOGLE_CLIENT_ID')[:20] + '...' if os.getenv('GOOGLE_CLIENT_ID') else 'MISSING')"
```

Should print: `Client ID: 1234...xyz` (truncated for safety).

---

## What happens next (handled in Phase 3 ship 2/3)

Once credentials are in `.env`:

1. You start the webapp: `uvicorn webapp:app --reload --host 0.0.0.0 --port 8000`
2. Open `localhost:8000/auth/gmail/start` in your browser
3. Browser redirects to Google's consent screen — sign in with your Gmail
4. Google asks: *"Job Tracker (personal) wants to read your Gmail. Allow?"* → click **Allow**
5. Browser redirects back to `localhost:8000/auth/gmail/callback`
6. The app stores your refresh token in the `oauth_tokens` table (gitignored DB — never leaves your machine)
7. Done — from now on the tracker can read Gmail on demand

After that, **Phase 3 ship 3/3** wires the parser + matcher + UI for actually syncing LinkedIn emails into your tracker.

---

## Troubleshooting

- **"This app isn't verified" warning during consent:** click **Advanced** → **Go to Job Tracker (personal) (unsafe)**. This warning shows for apps in "Testing" status. Safe since you're the developer and test user.
- **"redirect_uri_mismatch" error:** the URI in `.env` and the URI you registered in Step 4 must match **exactly** (including trailing slash or lack thereof). Most common cause of failure.
- **Can't find Gmail API in Library:** make sure you've selected the right project in the top dropdown.
- **Want to revoke access later:** go to https://myaccount.google.com/permissions, find "Job Tracker (personal)" in the list, click Remove Access. The tracker's existing tokens become invalid; just re-do `/auth/gmail/start` to re-grant.
- **Want to use a different Gmail account:** create a new Google Cloud project under that account, or add the second email as a Test User in this project.

When you've done Steps 1–6 (or if anything fails along the way), tell me in chat. We continue from Phase 3 ship 2/3.
