// Job Tracker Capture - popup script
// Reads the current page, sends content to the configured API endpoint.

const DEFAULT_API_URL = 'http://localhost:8001';

// ─── Boot: load saved settings + preview current page title ────────────────
chrome.storage.local.get(['apiUrl', 'apiToken'], (result) => {
  document.getElementById('api-url').value = result.apiUrl || DEFAULT_API_URL;
  document.getElementById('api-token').value = result.apiToken || '';

  // If no token saved, auto-expand the settings panel so user notices
  if (!result.apiToken) {
    document.getElementById('settings').classList.remove('collapsed');
  }
});

// Show the active tab's title as a preview
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  if (tabs[0]) {
    document.getElementById('page-title').textContent = tabs[0].title || tabs[0].url;
  }
});

// ─── Settings toggle ────────────────────────────────────────────────────────
document.getElementById('settings-toggle').addEventListener('click', () => {
  document.getElementById('settings').classList.toggle('collapsed');
});

// ─── Save settings ──────────────────────────────────────────────────────────
document.getElementById('save-btn').addEventListener('click', () => {
  const apiUrl = document.getElementById('api-url').value.trim().replace(/\/+$/, '');
  const apiToken = document.getElementById('api-token').value.trim();
  chrome.storage.local.set({ apiUrl, apiToken }, () => {
    showStatus('Settings saved.', 'ok');
    document.getElementById('settings').classList.add('collapsed');
  });
});

// ─── Capture flow ──────────────────────────────────────────────────────────
document.getElementById('capture-btn').addEventListener('click', async () => {
  const btn = document.getElementById('capture-btn');
  const viewLink = document.getElementById('view-link');
  viewLink.classList.remove('show');

  // Pull settings
  const { apiUrl, apiToken } = await new Promise(resolve =>
    chrome.storage.local.get(['apiUrl', 'apiToken'], resolve)
  );

  if (!apiUrl || !apiToken) {
    showStatus('Set the API endpoint and token first (Settings below).', 'err');
    document.getElementById('settings').classList.remove('collapsed');
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Capturing...';
  showStatus('Reading page...', 'info');

  try {
    // Get the active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.id) {
      showStatus('No active tab found.', 'err');
      resetButton();
      return;
    }

    // Skip chrome:// and other restricted URLs
    if (tab.url.startsWith('chrome://') || tab.url.startsWith('chrome-extension://')) {
      showStatus('Cannot capture from this type of page.', 'err');
      resetButton();
      return;
    }

    // Inject script to extract page content - aggressive extraction strategy:
    // 1. Click any "Show more" buttons to expand collapsed JD sections
    // 2. Wait a beat for the DOM to settle after the clicks
    // 3. Capture textContent (includes hidden DOM, unlike innerText)
    // 4. Extract any JSON-LD structured data (JobPosting schema)
    // 5. Return everything; server picks the best signal
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: async () => {
        // Step 1: click any "show more" / "see more" / "expand" buttons.
        // LinkedIn collapses the JD by default. Aggressively click anything
        // that looks like an expander.
        const expandPatterns = [
          'show more', 'see more', 'expand', 'read more', 'view more',
          'show all', 'see all', 'view all', 'show details', 'see details',
          'view details', 'show description', 'click to see',
        ];
        const expandSelectors = [
          'button', 'a', 'span[role="button"]', 'div[role="button"]',
          '[aria-expanded="false"]',
        ];
        document.querySelectorAll(expandSelectors.join(',')).forEach(el => {
          const txt = (el.innerText || el.textContent || el.getAttribute('aria-label') || '').toLowerCase().trim();
          if (expandPatterns.some(p => txt.includes(p)) && txt.length < 60) {
            try { el.click(); } catch (e) { /* ignore */ }
          }
        });

        // Step 2: longer wait for LinkedIn's slow React renders
        await new Promise(r => setTimeout(r, 800));

        // Step 3: second pass of clicking - some pages reveal more
        // expanders only after the first round of clicks
        document.querySelectorAll(expandSelectors.join(',')).forEach(el => {
          const txt = (el.innerText || el.textContent || el.getAttribute('aria-label') || '').toLowerCase().trim();
          if (expandPatterns.some(p => txt.includes(p)) && txt.length < 60) {
            try { el.click(); } catch (e) { /* ignore */ }
          }
        });
        await new Promise(r => setTimeout(r, 400));

        // Step 4: scroll through the page to trigger any lazy-loaded sections
        try {
          window.scrollTo(0, document.body.scrollHeight);
          await new Promise(r => setTimeout(r, 350));
          window.scrollTo(0, document.body.scrollHeight / 2);
          await new Promise(r => setTimeout(r, 200));
          window.scrollTo(0, 0);
        } catch (e) { /* ignore */ }

        // Step 4: extract JSON-LD structured data (the cleanest source if present)
        const jsonLdBlocks = [];
        document.querySelectorAll('script[type="application/ld+json"]').forEach(script => {
          try {
            const parsed = JSON.parse(script.textContent);
            jsonLdBlocks.push(parsed);
          } catch (e) { /* ignore parse errors */ }
        });

        // Step 5: grab meta tags (OpenGraph + standard meta description)
        const metaTags = {};
        document.querySelectorAll('meta').forEach(m => {
          const k = m.getAttribute('property') || m.getAttribute('name');
          const v = m.getAttribute('content');
          if (k && v) metaTags[k] = v;
        });

        return {
          url: window.location.href,
          title: document.title,
          // Visible text (cleaner formatting, respects line breaks)
          text: (document.body.innerText || '').slice(0, 80000),
          // All text including hidden elements (captures collapsed JDs)
          text_all: (document.body.textContent || '').slice(0, 100000),
          // JSON-LD blocks (jobPosting schema lives here on many sites)
          json_ld: jsonLdBlocks,
          // Meta tags (og:title, og:description, etc.)
          meta: metaTags,
        };
      },
    });

    if (!results || !results[0] || !results[0].result) {
      showStatus('Could not read page content.', 'err');
      resetButton();
      return;
    }

    const pageData = results[0].result;
    showStatus('Sending to Job Tracker...', 'info');

    // POST to the capture endpoint
    const response = await fetch(`${apiUrl}/extension/capture`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Extension-Token': apiToken,
      },
      body: JSON.stringify(pageData),
    });

    if (!response.ok) {
      const errText = await response.text().catch(() => '');
      showStatus(`Error ${response.status}: ${errText.slice(0, 100)}`, 'err');
      resetButton();
      return;
    }

    const data = await response.json();
    if (data.deduped) {
      showStatus(`Already captured. Job #${data.job_id}.`, 'info');
    } else {
      showStatus(`Captured. Job #${data.job_id} added to your leads.`, 'ok');
    }

    // Show "Open in Job Tracker" link
    viewLink.href = `${apiUrl}/jobs/${data.job_id}`;
    viewLink.classList.add('show');
    resetButton();
  } catch (e) {
    showStatus(`Error: ${e.message || String(e)}`, 'err');
    resetButton();
  }

  function resetButton() {
    btn.disabled = false;
    btn.textContent = 'Capture this page';
  }
});

function showStatus(msg, kind) {
  const el = document.getElementById('status');
  el.textContent = msg;
  el.className = `status ${kind || ''}`;
}
