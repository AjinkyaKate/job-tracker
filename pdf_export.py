"""Server-side HTML to PDF via Playwright (headless Chromium).

Why Playwright and not the browser's Save-as-PDF or html2pdf.js:
- Chromium's DevTools printToPDF (what page.pdf() calls) preserves clickable
  link annotations. The Chrome UI "Save as PDF" button bypasses this API and
  flattens links to dead text. html2pdf.js rasterises to an image, killing
  links AND text selection.
- Playwright renders real HTML/CSS, so the PDF matches the on-screen design,
  has selectable (ATS-parseable) text, and paginates cleanly.

Playwright + its Chromium are heavy. The import is lazy so the web app still
boots if they're missing (e.g. a host without Chromium). Callers get a
RuntimeError they can surface as a friendly message.
"""


def is_available() -> bool:
    """True if Playwright is importable. Does not verify Chromium is present."""
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


def html_to_pdf(html: str, *, margin_mm: float = 12.0) -> bytes:
    """Render an HTML string to PDF bytes using headless Chromium.

    Runs the Playwright SYNC API, so the caller must NOT be inside an asyncio
    event loop. In FastAPI, that means the calling route must be a plain
    `def` (Starlette runs it in a threadpool with no running loop), not an
    `async def`.

    Raises RuntimeError if Playwright/Chromium is unavailable or rendering
    fails, so the route can return a clean 503/500 instead of crashing.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright not installed. Run: pip install playwright "
            "&& playwright install chromium"
        ) from exc

    margin = f"{margin_mm}mm"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page()
                # set_content + networkidle so any web fonts / CDN CSS finish
                # loading before we snapshot to PDF.
                page.set_content(html, wait_until="networkidle")
                pdf_bytes = page.pdf(
                    format="A4",
                    print_background=True,
                    margin={"top": margin, "bottom": margin,
                            "left": margin, "right": margin},
                )
            finally:
                browser.close()
        return pdf_bytes
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"PDF generation failed: {exc}") from exc
