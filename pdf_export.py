"""Server-side HTML to PDF, with a two-engine strategy.

1. Playwright (headless Chromium) — best fidelity, preserves clickable link
   annotations and selectable (ATS-parseable) text. Used wherever Chromium is
   available (e.g. local dev).
2. xhtml2pdf (pure Python) — fallback for hosts WITHOUT a browser or cairo/
   system libs (e.g. Render's native Python runtime). Installs with plain pip,
   no system deps. Renders a subset of HTML/CSS and keeps <a href> links
   clickable in the PDF, which is what matters for a resume.

html_to_pdf() tries Chromium first and silently falls back to xhtml2pdf, so the
download works in both environments. Imports are lazy so the web app still boots
if neither engine is installed (the route then returns a clean 503).
"""

MARGIN_MM_DEFAULT = 12.0


def _playwright_importable() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


def _xhtml2pdf_importable() -> bool:
    try:
        import xhtml2pdf  # noqa: F401
        return True
    except ImportError:
        return False


def is_available() -> bool:
    """True if at least one PDF engine is importable."""
    return _playwright_importable() or _xhtml2pdf_importable()


def _render_playwright(html: str, margin_mm: float) -> bytes:
    """Chromium printToPDF — real HTML/CSS, clickable links, selectable text."""
    from playwright.sync_api import sync_playwright

    margin = f"{margin_mm}mm"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
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


def _render_xhtml2pdf(html: str, margin_mm: float) -> bytes:
    """Pure-Python fallback. Injects an @page rule for margins (Chromium gets
    margins from the API; xhtml2pdf needs them in CSS). Keeps <a href> links."""
    import io
    from xhtml2pdf import pisa

    page_css = f"@page {{ size: A4; margin: {margin_mm}mm; }}"
    # Put the @page rule first inside the existing <style> block; otherwise
    # prepend a small style block.
    if "<style>" in html:
        html = html.replace("<style>", "<style>\n  " + page_css + "\n", 1)
    else:
        html = "<style>" + page_css + "</style>" + html

    buf = io.BytesIO()
    status = pisa.CreatePDF(src=html, dest=buf, encoding="utf-8")
    if status.err:
        raise RuntimeError(f"xhtml2pdf reported {status.err} error(s)")
    data = buf.getvalue()
    if not data:
        raise RuntimeError("xhtml2pdf produced empty output")
    return data


def html_to_pdf(html: str, *, margin_mm: float = MARGIN_MM_DEFAULT) -> bytes:
    """Render HTML to PDF bytes. Prefer Chromium; fall back to xhtml2pdf.

    Must be called from a plain `def` route (not `async def`) because the
    Playwright sync API can't run inside a live asyncio loop.

    Raises RuntimeError only if BOTH engines are unavailable/failing, so the
    route can return a clean 503.
    """
    if _playwright_importable():
        try:
            return _render_playwright(html, margin_mm)
        except Exception:
            # Chromium present-but-broken (e.g. missing system libs): fall back.
            pass

    if _xhtml2pdf_importable():
        return _render_xhtml2pdf(html, margin_mm)

    raise RuntimeError(
        "No PDF engine available. Install one of: "
        "playwright (+ chromium) or xhtml2pdf."
    )
