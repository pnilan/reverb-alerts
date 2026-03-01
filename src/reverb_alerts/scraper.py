import logging
import os
import re
from urllib.parse import quote

from firecrawl import FirecrawlApp

from reverb_alerts.models import ReverbCondition

logger = logging.getLogger(__name__)

CONDITION_SLUGS: dict[ReverbCondition, str] = {
    ReverbCondition.BRAND_NEW: "brand-new",
    ReverbCondition.MINT: "mint",
    ReverbCondition.EXCELLENT: "excellent",
    ReverbCondition.VERY_GOOD: "very-good",
    ReverbCondition.GOOD: "good",
    ReverbCondition.B_STOCK: "b-stock",
    ReverbCondition.POOR: "poor",
    ReverbCondition.NON_FUNCTIONING: "non-functioning",
}

BOILERPLATE_PATTERNS = [
    r"!\[.*?\]\(.*?\)",                          # image tags
    r"\[Close\]\(.*?\)",                         # close links
    r"Related searches.*?(?=\n\n-|\Z)",          # related searches block
    r"Reverb Bump",                              # bump badges
    r"\d+-Day Return Policy",                    # return policy text
    r"Free Shipping",                            # shipping badges
    r"Great Value",                              # value badges
    r"Recently Listed",                          # recently listed badges
    r"Preferred Seller",                         # seller badges
]

BOILERPLATE_RE = re.compile("|".join(BOILERPLATE_PATTERNS), re.DOTALL)


def _clean_markdown(markdown: str) -> str:
    # cut everything after the listings end (sidebar/footer)
    # the listings section ends with "## " or "### " headers like "Shop Gear", "Sort by", etc.
    cutoff_patterns = [
        r"\n## \n",                          # empty heading (separator)
        r"\n### Shop Gear",                  # footer start
        r"\n### Sort by",                    # sidebar filter start
        r"\n#### Let the Gear Come to You",  # save search section
        r"\nFilter Your Search",             # filter sidebar
    ]
    for pattern in cutoff_patterns:
        match = re.search(pattern, markdown)
        if match:
            markdown = markdown[:match.start()]

    # strip boilerplate patterns
    cleaned = BOILERPLATE_RE.sub("", markdown)

    # truncate tracking params from URLs (?bk=...)
    cleaned = re.sub(r"\?bk=[^)\s]*", "", cleaned)

    # strip "In X Other Cart(s)" and "Price Drop" lines
    cleaned = re.sub(r"In \d+ Other Carts?\n?", "", cleaned)
    cleaned = re.sub(r"Price Drop\n?", "", cleaned)
    cleaned = re.sub(r"Local Pickup\n?", "", cleaned)

    # strip "Originally $X, now $Y ($Z price drop)" lines (keep just the current price)
    cleaned = re.sub(r"Originally \$[\d,.]+, now \$[\d,.]+ \(\$[\d,.]+ price drop\)\n?", "", cleaned)
    cleaned = re.sub(r"\$[\d,.]+ price drop\n?", "", cleaned)

    # collapse multiple blank lines into one
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # strip lines that are only whitespace
    cleaned = "\n".join(line for line in cleaned.splitlines() if line.strip())

    return cleaned


def scrape_reverb(query: str, max_price: float, location: str | None = None, conditions: list[ReverbCondition] | None = None) -> str | None:
    app = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])

    min_price = int(max_price // 2)
    url = f"https://reverb.com/marketplace?query={quote(query)}&sort=price%7Casc&price_min={min_price}&price_max={int(max_price)}&exclude_local_pickup_only=true"
    if location:
        url += f"&item_region={quote(location)}"
    if conditions:
        for condition in conditions:
            url += f"&condition%5B%5D={CONDITION_SLUGS[condition]}"

    logger.info("Scraping %s", url)
    result = app.scrape(
        url,
        formats=["markdown"],
        only_main_content=True,
        wait_for=5000,
        actions=[
            {"type": "wait", "milliseconds": 3000},
            {"type": "scroll", "direction": "down", "amount": 3},
        ],
    )

    raw = result.markdown or ""
    logger.debug("Firecrawl response length: %d chars", len(raw))

    cleaned = _clean_markdown(raw)
    logger.debug("Cleaned markdown length: %d chars (%.0f%% reduction)", len(cleaned), (1 - len(cleaned) / len(raw)) * 100 if raw else 0)

    return cleaned
