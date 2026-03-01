# reverb-alerts

A CLI tool that monitors [Reverb.com](https://reverb.com) for musical gear deals and notifies you via GitHub Issues. Runs on a GitHub Actions cron schedule — free for public repos.

## How It Works

1. Scrapes Reverb marketplace search results using [Firecrawl](https://firecrawl.dev)
2. Extracts structured listing data with a [PydanticAI](https://ai.pydantic.dev) agent
3. Filters listings by price, shipping, condition, and seller location
4. Creates a GitHub Issue when a match is found (with deduplication)

## Setup

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)

### Install dependencies

```sh
uv sync
```

### Environment variables

| Variable | Description |
|---|---|
| `FIRECRAWL_API_KEY` | API key for Firecrawl web scraping |
| `ANTHROPIC_API_KEY` | API key for the PydanticAI extraction agent |

## Configuration

Define watches in `watches.yaml`:

```yaml
watches:
  - name: "Line 6 HX Stomp"
    query: "Line 6 HX Stomp"
    max_price: 400.00
    include_shipping: true
    location: "US"
    conditions:
      - "Very Good"
      - "Excellent"
      - "Mint"
```

| Field | Required | Default | Description |
|---|---|---|---|
| `name` | yes | — | Display name for notifications |
| `query` | yes | — | Search keywords on Reverb |
| `max_price` | yes | — | Price threshold in USD |
| `include_shipping` | no | `false` | Compare `max_price` against price + shipping |
| `location` | no | any | Seller location filter (e.g. `US`, `UK`, `EU`) |
| `conditions` | no | any | Acceptable conditions: `Brand New`, `Mint`, `Excellent`, `Very Good`, `Good`, `B-Stock`, `Poor Condition`, `Non Functioning` |

## Usage

```sh
# Preview matches without creating issues
uv run reverb-alerts --dry-run

# Check for deals and create GitHub Issues
uv run reverb-alerts --execute

# Use a custom config file
uv run reverb-alerts --dry-run --config path/to/watches.yaml

# Enable debug logging (includes httpx traffic)
uv run reverb-alerts --dry-run --debug
```

## GitHub Actions

The included workflow runs every 6 hours and can be triggered manually. Add `FIRECRAWL_API_KEY` and `ANTHROPIC_API_KEY` as repository secrets.

```yaml
on:
  schedule:
    - cron: '0 */6 * * *'
  workflow_dispatch: {}
```
