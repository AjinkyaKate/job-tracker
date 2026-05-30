# Job Tracker Capture (Chrome Extension)

One-click job posting capture from any site. Naukri, Indeed, LinkedIn, Wellfound, company career pages, anywhere. Click the extension icon → page is saved as a lead in your Job Tracker app.

## How to install (local development)

Chrome / Brave / Edge / any Chromium browser. ~30 seconds.

1. Open `chrome://extensions` in your browser.
2. Turn on **Developer mode** (top right toggle).
3. Click **Load unpacked**.
4. Pick this folder: `<your-path>/job-tracker/extension/`
5. The extension appears in your toolbar. Pin it (puzzle-piece icon → pin) so it's always visible.

## First-time setup

1. Click the extension icon in your toolbar.
2. Open the **Settings** panel inside the popup.
3. Set the **API endpoint**:
   - Local dev: `http://localhost:8001`
   - Production: `https://job-tracker-bmhy.onrender.com`
4. Set the **API token**: must match the `EXTENSION_API_TOKEN` env var on the server.
   - Local dev: set it in your terminal before starting uvicorn:
     ```
     export EXTENSION_API_TOKEN=local-dev-token
     ```
     Then paste `local-dev-token` into the extension settings.
   - Production: set it in Render env vars, paste the same value here.
5. Click **Save settings**.

## How to use

1. Browse to any job posting on any site.
2. Click the Job Tracker extension icon.
3. Click **Capture this page**.
4. Done. A new lead appears in your Job Tracker app at `/leads`.

The page URL, title, and full text body are sent to the server. The server stores the raw text so resume tailoring can use it later.

## What gets sent

- URL of the page
- Page title (whatever's in `<title>`)
- Full visible body text (capped at 50,000 chars)
- Your API token in the `X-Extension-Token` header

The server stores this as a new job row with `status=lead` and `source=extension`. If you capture the same URL twice, the second capture is recognized as a duplicate and returns the existing job ID.

## Permissions explained

- `activeTab` — read the page you're currently looking at, only when you click the extension
- `scripting` — inject the page-reader script into the active tab
- `storage` — remember your API endpoint and token across sessions
- `host_permissions` for localhost:8001 and the Render URL — so the extension can POST to your Job Tracker

The extension does NOT read pages in the background. It only fires when you click.

## Troubleshooting

**"Cannot capture from this type of page"**: You're on a `chrome://` URL (Chrome settings, new tab, etc.). Extensions can't read those. Navigate to a real website.

**Error 401: invalid_token**: API token in extension settings doesn't match the server's `EXTENSION_API_TOKEN` env var. Double-check both sides.

**Error 503: extension_not_configured**: Server doesn't have `EXTENSION_API_TOKEN` set. Set it on the server side (env var) and restart.

**Error 400: missing_url or missing_text**: The page didn't return readable text. Some single-page apps need a moment to render. Wait, then click capture.

**Nothing happens when I click capture**: Open Chrome DevTools (right-click the popup → Inspect popup) and check the console for JavaScript errors.
