from pydantic import BaseModel
from pydantic_ai import Agent

from reverb_alerts.config import Watch
from reverb_alerts.models import ReverbListing


class ListingResults(BaseModel):
    listings: list[ReverbListing]


SYSTEM_PROMPT = (
    "You are a data extraction agent. Given markdown content from a Reverb.com "
    "marketplace page, extract all product listings into structured data. "
    "For each listing, extract the title, price (as a float in USD), "
    "shipping cost (as a float, or null if free/not listed), "
    "seller location (or null if not shown), the listing URL, "
    "and the condition (one of: Brand New, Mint, Excellent, Very Good, "
    "Good, B-Stock, Poor Condition, Non Functioning — or null if not shown)."
)


def _get_agent() -> Agent[None, ListingResults]:
    return Agent(
        "anthropic:claude-haiku-4-5-20251001",
        output_type=ListingResults,
        instructions=SYSTEM_PROMPT,
    )


def parse_listings(markdown: str) -> list[ReverbListing]:
    agent = _get_agent()
    result = agent.run_sync(f"Extract all listings from this Reverb marketplace page:\n\n{markdown}")
    return result.output.listings


def filter_listings(listings: list[ReverbListing], watch: Watch) -> list[ReverbListing]:
    matches = []
    for listing in listings:
        effective_price = listing.price
        if watch.include_shipping and listing.shipping_cost is not None:
            effective_price += listing.shipping_cost

        if effective_price > watch.max_price:
            continue

        if watch.conditions and listing.condition not in watch.conditions:
            continue

        if watch.location and listing.seller_location:
            if watch.location.lower() not in listing.seller_location.lower():
                continue

        matches.append(listing)

    return matches
