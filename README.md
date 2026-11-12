# 📰 AI Daily News Aggregator

An automated, zero-cost 24/7 news aggregation and summarization system powered by **Python**, **Gemini API**, **GitHub Actions**, and **GitHub Pages**.

This project acts as a professional international and domestic news editor—automatically fetching RSS feeds, filtering out outdated news, summarizing top stories with AI resilience (automatic retry & graceful fallback), and publishing a beautifully formatted static web page.

---

## 🏛️ 1. Project Directory Structure

```text
news-aggregator/
├── .github/
│   └── workflows/
│       └── update_news.yml   # Automated cron workflow running twice daily on GitHub Actions
├── main.py                   # Core script: RSS scraping, Gemini API processing, Fallback handling & HTML rendering
├── requirements.txt          # Python dependencies
├── news.json                 # Historical archive of past newsletters (auto-generated, up to 30 days)
├── index.html                # Static web page displaying the latest newsletter (auto-generated)
└── README.md                 # Project documentation

```

*(Note: `news.json` and `index.html` are automatically generated and tracked by Git to preserve your newsletter history and serve the live site).*

---

## 🔄 2. Workflow Architecture & Resilience

The system runs completely autonomously on a scheduled cron job **twice daily** (at **5:30 AM** and **12:30 PM ICT** / **22:30** & **05:30 UTC**) or can be triggered manually by the repository owner:

```text
[ GitHub Actions Cron Trigger ] (Twice daily: 5:30 AM & 12:30 PM ICT)
              │
              ▼
[ Spin up Virtual Python Environment (3.13) ]
              │
              ▼
[ 1. Fetch Raw News from RSS Feeds ] (Reuters, BBC, Financial Times, VnExpress, Tuổi Trẻ, etc.)
              │
              ▼
[ 2. Call Gemini API (gemini-3.8-flash) with Retry Mechanism ]
      ├── 🟢 Success: Process Markdown, Deduplicate & Summarize
      └── 🔴 High Demand / Failure: Exponential Backoff Retry (30s -> 60s -> 120s)
              │
              ▼
[ 3. Handle Output & Fallback Logic ]
      ├── 🟢 API Success  ──> Save new edition to news.json & Render index.html
      └── 🔴 API Overload ──> Fetch latest successful edition from news.json & Render with status banner
              │
              ▼
[ 4. GitHub Actions Automatically Commits & Pushes Changes ]
              │
              ▼
[ 🌐 GitHub Pages Live Site Update ]

```

---

## ⚡ 3. Key Features

* **AI-Powered Editorial Control:** Uses Gemini AI (`gemini-3.8-flash`) to synthesize raw RSS feeds into an objective, professional newsletter format.
* **Smart Retry & Fallback Mechanism:** Includes exponential delay retry (`30s`, `60s`, `120s`) for high-demand API spikes. If the API fails completely, it gracefully renders the last successful newsletter from `news.json` with a notice banner—preventing site breakage or blank pages.
* **Strict Time & Quality Filtering:** Prioritizes breaking news within the last 24 hours while discarding outdated articles.
* **Multi-Region & Multi-Domain Coverage:** Spans World, Asia, and Vietnam across Economics/Investments, Politics/Society, Tech/Culture, and Climate/Environment.
* **Historical Archive:** Automatically maintains a rolling history of the last 30 daily editions via `news.json`.
* **100% Free & Secure Hosting:** Runs entirely on GitHub Actions and GitHub Pages with zero server costs and protected API quotas (no public manual triggers on UI).

---

## 🚀 4. Quick Setup Guide

### Step 1: Get your Gemini API Key

Visit [Google AI Studio](https://aistudio.google.com/) to generate your Gemini API key.

### Step 2: Configure GitHub Repository Secrets

1. Go to your GitHub repository > **Settings** > **Secrets and variables** > **Actions**.
2. Click **New repository secret**.
3. Name: `GEMINI_API_KEY`
4. Value: Paste your Google AI Studio API key.

### Step 3: Grant Workflow Permissions

1. Go to **Settings** > **Actions** > **General**.
2. Scroll down to **Workflow permissions**.
3. Select 👉 **Read and write permissions** and click **Save**.

### Step 4: Enable GitHub Pages

1. Go to **Settings** > **Pages**.
2. Under **Build and deployment**, set **Source** to **Deploy from a branch**.
3. Choose the `main` branch and `/ (root)` folder, then click **Save**.

---

## 📜 5. License & Attribution

Powered by Python, Google Gemini AI, and GitHub Pages. Built for personal automated daily reading.
