# 📰 AI Daily News Aggregator

An automated, zero-cost 24/7 news aggregation and summarization system powered by **Python**, **Gemini API**, **GitHub Actions**, and **GitHub Pages**.

This project acts as a professional international and domestic news editor—automatically fetching RSS feeds, filtering out outdated news, summarizing top stories, and publishing a beautifully formatted static web page.

---

## 🏛️ 1. Project Directory Structure

```text
news-aggregator/
├── .github/
│   └── workflows/
│       └── update_news.yml   # Automated cron workflow running on GitHub Actions
├── main.py                   # Core script: RSS scraping, Gemini API processing, and rendering
├── requirements.txt          # Python dependencies
├── news.json                 # Historical archive of past newsletters (auto-generated)
├── index.html                # Static web page displaying the latest newsletter (auto-generated)
└── README.md                 # Project documentation
```

*(Note: `news.json` and `index.html` are automatically generated and tracked by Git to preserve your newsletter history and serve the website).*

---

## 🔄 2. Workflow Architecture

The system runs completely autonomously on a scheduled cron job (every day at 00:00 UTC / 7:00 AM ICT) or can be triggered manually:

```text
[ GitHub Actions Cron Trigger ] (Scheduled / Manual Run)
              │
              ▼
[ Spin up Virtual Python Environment ]
              │
              ▼
[ 1. Fetch Raw News from RSS Feeds ] (Reuters, BBC, VnExpress, TechCrunch, etc.)
              │
              ▼
[ 2. Send Raw Data + Professional Editor Prompt to Gemini API ]
              │
              ▼
[ 3. Gemini Processing: Deduplicate, Summarize (2-4 sentences), Categorize (3 Regions, 4 Domains) ]
              │
              ▼
[ 4. Python Updates History (news.json) & Renders Web UI (index.html) ]
              │
              ▼
[ 5. GitHub Actions Automatically Commits & Pushes Changes ]
              │
              ▼
[ 🌐 GitHub Pages Live Site Update ]

```

---

## 🚀 3. Quick Setup Guide

### Step 1: Get your Gemini API Key

Visit [Google AI Studio](https://aistudio.google.com/) to generate a free API key.

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

### Step 5: Test Run

Go to the **Actions** tab on GitHub, select the `Auto Generate Daily News` workflow, and click **Run workflow** to generate your first AI-curated newsletter!

---

## ⚙️ Features

* **AI-Powered Editorial Control:** Uses Gemini to synthesize raw RSS feeds into an objective, professional newsletter format.
* **Strict Time & Quality Filtering:** Prioritizes breaking news within the last 24 hours while discarding outdated articles.
* **Multi-Region & Multi-Domain Coverage:** Spans World, Asia, and Vietnam across Economics, Politics, Tech/AI, and Climate/Environment.
* **Historical Archive:** Automatically maintains a rolling history of the last 30 daily editions via `news.json`.
* **100% Free Hosting:** Operates entirely on GitHub Actions and GitHub Pages with zero server maintenance costs.
