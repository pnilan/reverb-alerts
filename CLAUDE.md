# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Reverb-alerts is a CLI tool that monitors Reverb.com for musical gear deals. It runs on a GitHub Actions cron schedule, scrapes Reverb marketplace pages using Firecrawl, extracts listings with a PydanticAI agent, and creates GitHub Issues when listings match configured price/condition thresholds. Configuration is via `watches.yaml`.

## Tech Stack

- **Python >=3.10**, managed with **uv**
- **Firecrawl** (`firecrawl-py`) for web scraping
- **PydanticAI** with Anthropic model for extracting structured listing data from scraped markdown
- **Pydantic** for data models
- **Click** for CLI
- **PyYAML** for config loading
- **GitHub CLI (`gh`)** for issue creation (pre-installed on Actions runners)

## Commands

- `uv run reverb-alerts check` — run the deal checker
- `uv run reverb-alerts check --dry-run` — check without creating GitHub Issues
- `uv sync` — install/sync dependencies

## Architecture

```
watches.yaml → config.py → cli.py → scraper.py → parser.py → notify.py
                (load)      (loop)   (firecrawl)  (pydantic-ai) (gh issue)
```

1. **Config** (`config.py`): loads `watches.yaml`, returns validated watch definitions (query, max_price, include_shipping, location, conditions)
2. **Scraper** (`scraper.py`): uses Firecrawl to fetch Reverb marketplace search results as markdown
3. **Parser** (`parser.py`): PydanticAI agent extracts `list[ReverbListing]` from scraped markdown, then filters by price/shipping/location/condition
4. **Notifier** (`notify.py`): creates GitHub Issues via `gh issue create` subprocess, deduplicates by checking for open issues with same title
5. **CLI** (`cli.py`): Click entrypoint, `--config` flag for watches.yaml path

## Key Environment Variables

- `FIRECRAWL_API_KEY` — Firecrawl API access
- `ANTHROPIC_API_KEY` — used by PydanticAI agent
