# Market Intelligence News Feed

Automated news discovery and summarization platform for the Equinix CRO organization's Market Intelligence team.

## Overview

Replaces manual competitor website monitoring with an automated pipeline that discovers, cleans, summarizes, and tags data center industry news articles.

## Architecture

```
Layer 1 (Source) → Layer 2 (Processing) → Layer 3 (Storage) → Layer 4 (UI)
```

- **Layer 1 — Fetch:** Discovers articles from competitor/industry news sites via Jina Reader
- **Layer 2 — Processing:** Cleans raw content, AI summarization (Gemini 2.5 Flash), auto-tagging
- **Layer 3 — Storage:** PostgreSQL + SQLAlchemy *(in progress)*
- **Layer 4 — UI:** News feed dashboard with role-based access *(planned)*

## Usage

```bash
# All sites
python -m newsfeed.run

# Single site
python -m newsfeed.run --site dcd

# Date range
python -m newsfeed.run --site dcd --from 2026-02-19 --to 2026-02-20

# Corporate proxy (skip SSL verification)
python -m newsfeed.run --site dcd --no-verify-ssl
```

## Setup

1. Copy `.env.example` to `.env` and fill in your API keys:
   ```
   GOOGLE_API_KEY=<your key>
   DATABASE_URL=postgresql://newsfeed:newsfeed@db:5432/newsfeed
   ```

2. Run with Docker:
   ```bash
   docker-compose up
   ```

## Current Sources

- [DataCenterDynamics](https://datacenterdynamics.com/en/news/)

## Requirements

See `newsfeed/requirements.txt`
