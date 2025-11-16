# Metri — UI Refresh (feature/ui-refresh)

This branch contains a runnable Flask wrapper that serves the UI prototype located under `web/`.

How to run locally

1. Create a Python virtualenv (recommended):

   python -m venv .venv
   source .venv/bin/activate     # Linux/macOS
   .venv\Scripts\activate      # Windows

2. Install dependencies:

   pip install -r requirements.txt

3. Run the app:

   python main.py

4. Open http://127.0.0.1:5000/ in your browser. The dashboard is served at `/dashboard` (or `/run_tio`).

What this provides

- A small Flask entrypoint `main.py` that serves the prototype templates in `web/templates` and static assets in `web/static`.
- Pages: Dashboard, Ćwiczenia, Metronom, Detektor.
- A theme CSS and a small JS module to toggle de-emphasis and theme (persisted in localStorage).

Notes

- This wrapper is intentionally non-invasive: it doesn't modify your existing application code. Use it to review and iterate on the new UI. When you're ready, the styles and template changes can be integrated into your main app or the current application entrypoint.