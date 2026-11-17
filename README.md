# 📰 AI Daily News Aggregator

Zero-cost daily news digest: **RSS → Gemini (free API key) → `site/news.json` → static page**. A **Cloudflare Worker** triggers the job on time, **GitHub Actions** runs it, and **Cloudflare** serves the site.

## How it works

```text
Cloudflare Worker (Cron Trigger, 05:17 & 11:17 ICT)
  └─ POST workflow_dispatch  {slot: morning|midday, force: false}
GitHub Actions: update_news.yml
  └─ main.py
       1. Fetch ~17 RSS feeds in parallel, drop stale/duplicate items
       2. Send titles to Gemini (retry on 429/5xx only, fallback models)
       3. Replace citation codes [#12] with real links (the model never writes URLs);
          stories left without a valid source link are dropped
       4. Render Markdown -> sanitized HTML (markdown-it-py + nh3)
       5. Save to site/news.json  (keeps the 2 newest sessions only)
  └─ commit site/news.json to main
Cloudflare (Git integration) deploys ./site on every push to main
```

- **Sessions:** the site keeps the 2 most recent runs, for example `16/11/2026 sáng` and `16/11/2026 trưa`, and shows the latest one by default. Each session is keyed by date + slot, so re-running the same slot overwrites it.
- **Already-seen stories are greyed out:** when viewing the latest session, stories that share a source link with the previous session get a muted style and an "Đã có ở bản trước" badge, with a counter of new vs already-seen stories. Two different articles about the same event are not detected.
- **If fetching or Gemini fails**, `main.py` keeps the old sessions, records `last_run: failed` in `news.json`, and the page shows the latest saved session with a warning banner. The Actions run is marked failed so GitHub emails you.
- **Backup schedule:** the workflow also keeps GitHub's own `schedule`, which often starts hours late. If the Worker already created the session, `main.py` skips it (`SKIP_IF_EXISTS`) and does not call Gemini again.

## Repository layout

```text
.github/workflows/update_news.yml   # workflow_dispatch (Worker) + backup schedule
main.py                             # fetch, summarize, render, save
requirements.txt
site/                               # the only folder served publicly
  index.html  app.js  news.json
worker/index.js                     # Cron Trigger -> workflow_dispatch, and static assets
wrangler.jsonc                      # Worker config (assets, crons, vars)
```

## `site/news.json` schema

```json
{
  "schema": 2,
  "last_run": { "at": "2026-11-16T11:17:42+07:00", "status": "ok" },
  "editions": [
    { "id": "2026-11-16-midday", "date": "2026-11-16", "slot": "midday", "label": "Bản trưa",
      "generated_at": "2026-11-16T11:17:42+07:00", "model": "gemini-3.8-flash",
      "content": "# markdown...", "html": "<h1>...</h1>" }
  ]
}
```

## Setup (do these in order)

1. **Gemini key:** create one at [Google AI Studio](https://aistudio.google.com/). In the GitHub repo go to **Settings → Secrets and variables → Actions** and add the secret `GEMINI_API_KEY`. Optional variable `GEMINI_MODELS` (one comma-separated string, tried in order).
2. **GitHub permissions:** **Settings → Actions → General → Workflow permissions** = *Read and write*.
3. **Create a GitHub token for the Worker:** GitHub → *Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token*.
   - Repository access: **Only select repositories** → `web-daily-news`
   - Permissions → Repository → **Actions: Read and write** (Metadata read is added automatically)
   - Set an expiry and put a reminder to renew it; when it expires the Worker logs HTTP 401.
4. **Create the Cloudflare Worker from the repo:** Cloudflare dashboard → *Workers & Pages → Create → Import a repository* → pick `web-daily-news`, branch `main`. Keep the deploy command `npx wrangler deploy`. Cloudflare reads `wrangler.jsonc`, so the cron triggers and the `./site` assets are set up automatically. The `name` in `wrangler.jsonc` must match the Worker name you chose in the dashboard (currently `daily-news`). Make sure `wrangler.jsonc` is already on `main` before creating the Worker; if it is missing, Wrangler tries to auto-detect the project (it picks Jekyll because of `_config.yml`) and the build fails. If you hit that, push the file and use *Retry build*.
5. **Add the token as a Worker secret:** the Worker's *Settings → Variables and Secrets → Add*, type **Secret**, name `GH_DISPATCH_TOKEN`, value = the token from step 3. Redeploy if asked.
6. **Verify:**
   - Actions tab → *Run workflow* once (leave the defaults). A commit from `github-actions[bot]` should appear and Cloudflare should start a new build.
   - In Cloudflare the Worker's **Settings → Trigger Events** should list both crons; **Observability → Logs** shows each scheduled run.
7. **Only after steps 1-6 work**, you can delete the old `gh-pages` branch and turn off GitHub Pages. Until then the old Pages site keeps serving the old files.

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
GEMINI_API_KEY=your_key python main.py             # updates site/news.json
python -m http.server 8000 --directory site        # open http://localhost:8000
```

`index.html` loads `news.json` with `fetch`, so open it through a local server, not `file://`.

To test the Worker's cron locally, put `GH_DISPATCH_TOKEN=...` in `.dev.vars` (git-ignored), run `npx wrangler dev --test-scheduled`, then call `curl "http://localhost:8787/__scheduled?cron=17+22+*+*+*"`. This triggers a real workflow run.

## Notes

- Never commit `.env` or `.dev.vars` (both are in `.gitignore`).
- If you change the times, update all three places: `triggers.crons` in `wrangler.jsonc`, `SLOT_BY_CRON` in `worker/index.js`, and the backup `schedule` in the workflow.
- LLM output is untrusted: raw HTML is escaped by markdown-it, then `nh3` whitelists tags and only allows http/https links. The page has no third-party scripts, and its CSP only allows `script-src 'self'`.
- The page shows a "stale" banner if the latest session is older than 36 hours.
- `_config.yml` (Jekyll settings from the GitHub Pages setup) is no longer used and can be deleted.
