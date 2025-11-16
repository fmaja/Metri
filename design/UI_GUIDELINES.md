# UI Guidelines — Metri (proposed)

Goal
- Modernize the app: professional, intuitive, consistent, and accessible.
- Keep colors friendly and musical (teal/mint primary, deep accent purple, warm gold, fresh green).
- Provide a de-emphasis mode that reduces contrast/saturation of non-primary UI elements for focus, and ensure it works for both light and dark themes.

Color tokens
- --primary:    #18a79a  (teal) — brand/action
- --accent:     #5b2b6f  (deep purple) — icons/highlight
- --muted:      #9aa8a6  (cool gray) — less important text
- --warm:       #d4a72a  (mustard/gold) — progress/secondary CTA
- --positive:   #4caf50  (green) — success
- --bg:         #f5f5f6  (light background)
- --card-bg:    #ffffff
- Use CSS variables for light/dark overrides.

Typography
- Base font-size: 16px
- Headings: Inter or system sans, bold weights for h1/h2
- Use consistent spacing scale: 4 / 8 / 16 / 24 / 32

Components (summary)
- Header: left logo + centered page title + right settings icon. Clean rounded rectangle or pill background.
- Card grid: evenly spaced cards with subtle elevation, consistent radii, large icon + label.
- Progress: rounded full-width bar with tokenized color for progress fill.
- Buttons: primary (filled), secondary (outline), small circular icon buttons.
- Feedback: non-blocking toasts and small callouts (speech bubbles only for playful UX; use subtle animations).

Accessibility
- Maintain contrast ratio >= 4.5:1 for primary text.
- Keyboard focus visible for all interactive elements.
- Respect user prefers-color-scheme and allow manual overrides.

De-emphasis pattern
- A root toggle (data-deemphasized="true" on html element) that:
  - reduces saturation and contrast of background and secondary UI elements
  - lowers opacity for decorative visuals
  - keeps primary calls-to-action at full emphasis
- This can be toggled from the settings menu and persists.

Integration notes
- Add the CSS file site-wide and import the JS toggle module near the main app entry.
- Add web/static/js/ui-mode.js near your site's bottom (defer) so it initializes before user interaction.
- Replace inline styles with tokens where possible.
