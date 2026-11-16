# 📰 AI Daily News Aggregator

Zero-cost daily news digest: **RSS → Gemini (free API key) → `news.json` → static `index.html`**, scheduled by **GitHub Actions** and served by **GitHub Pages**.

## How it works

```text
GitHub Actions cron (05:17 & 11:17 ICT)
  └─ main.py
       1. Fetch ~17 RSS feeds in parallel, drop stale/duplicate items
       2. Send titles to Gemini (retry on 429/5xx only, optional fallback model)
       3. Replace citation codes [#12] with real links (the model never writes URLs);
          stories left without a valid source link are dropped
       4. Render Markdown -> sanitized HTML (markdown-it-py + nh3)
       5. Save to news.json  (keeps the 2 newest editions only)
  └─ commit news.json to main  (so history survives between runs)
  └─ publish index.html + app.js + news.json to gh-pages
```

- **Latest edition** is shown by default; the previous one is available via the tab.
- **If fetching or Gemini fails**, `main.py` keeps the old editions, records `last_run: failed` in `news.json`, and `index.html` shows the latest saved edition with a warning banner. The Actions run is marked failed so GitHub emails you.
- **Editions** are keyed by date + slot (`morning` before 09:00 ICT, otherwise `midday`). Re-running within the same slot overwrites that edition instead of adding a new one.

## `news.json` schema

```json
{
  "schema": 2,
  "last_run": { "at": "2026-11-16T11:17:42+07:00", "status": "ok" },
  "editions": [
    { "id": "2026-11-16-midday", "date": "2026-11-16", "slot": "midday", "label": "Bản trưa",
      "generated_at": "2026-11-16T11:17:42+07:00", "model": "gemini-3.8-flash", "content": "# markdown...", "html": "<h1>...</h1>" }
  ]
}
```

The legacy format (`[{date, content}]`) is still read and gets migrated on the next successful run.

## Setup

1. Create a key at [Google AI Studio](https://aistudio.google.com/).
2. Repo **Settings → Secrets and variables → Actions**: add secret `GEMINI_API_KEY`.
   Optional variable `GEMINI_MODELS` (comma-separated; tried in order, later ones act as fallback).
3. **Settings → Actions → General → Workflow permissions**: *Read and write*.
4. **Settings → Pages**: *Deploy from a branch* → `gh-pages` / `(root)`.
5. Run once from the **Actions** tab (*Run workflow*) to verify.

## Run locally

```bash
pip install -r requirements.txt
GEMINI_API_KEY=your_key python main.py     # updates news.json
python -m http.server 8000                 # open http://localhost:8000
```

`index.html` loads `news.json` with `fetch`, so open it through a local server, not `file://`.

## Notes

- Never commit `.env` (already in `.gitignore`).
- LLM output is untrusted: raw HTML is escaped by markdown-it, then `nh3` whitelists tags and only allows http/https links. The page has no third-party scripts, and its CSP only allows `script-src 'self'`.
- GitHub cron may start a few minutes late, and scheduled workflows can be auto-disabled after long repo inactivity; the page shows a "stale" banner if the latest edition is older than 36 hours.
