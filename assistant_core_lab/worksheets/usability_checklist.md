# Lab 7 — Usability checklist (tick before your user test)

Owner: @thanhhuong107 · Checked on: 2026-11-23

- [x] The first screen says what the assistant can do, with example questions
- [x] Empty or too-long input shows a friendly message (not a crash)
- [x] While waiting, the user sees "Thinking…"
- [x] Every answer from documents shows its sources
- [x] "I don't know" answers tell the user who can help (escalation)
- [x] If the backend is down, the page says so clearly
- [x] Each answer has 👍 / 👎, and clicking gives a "thanks" message
- [x] The page says it is an AI assistant
- [x] Text is readable (size, contrast); buttons have clear labels
- [x] Works on a phone-width window

## Verification evidence

- `python -m pytest -q tests/test_ui.py tests/test_ui_app.py tests/test_api_client.py`: 42 passed.
- Browser check at a 390 × 844 viewport: no horizontal overflow (`innerWidth = scrollWidth = 390`); heading, backend error, welcome message and input label remained readable.
- Source inspection confirmed the `Thinking…` spinner, example questions and AI disclosure on the first screen.
