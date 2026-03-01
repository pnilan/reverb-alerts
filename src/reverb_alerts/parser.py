import logging
import re

from pydantic import BaseModel
from pydantic_ai import Agent

from reverb_alerts.config import Watch
from reverb_alerts.models import ReverbListing

logger = logging.getLogger(__name__)


class ListingResults(BaseModel):
    listings: list[ReverbListing]


SYSTEM_PROMPT = (
    "You are a data extraction agent. Given markdown content from a Reverb.com "
    "marketplace page, extract all product listings into structured data. "
    "For each listing, extract the title, price (as a float in USD), "
    "shipping cost (as a float, or null if free/not listed), "
    "seller location (or null if not shown), the listing URL, "
    "and the condition (one of: Brand New, Mint, Excellent, Very Good, "
    "Good, B-Stock, Poor Condition, Non Functioning — or null if not shown). "
    "For each listing, set is_primary_product to true if the listing is the "
    "actual main product/instrument/unit being searched for, and false if it is "
    "an accessory, replacement part, adapter, cable, case, cover, knob, "
    "footswitch, or other peripheral item. For example, if searching for "
    "'Boss RE-202', an AC adapter for the RE-202 is NOT a primary product."
)


def _get_agent() -> Agent[None, ListingResults]:
    return Agent(
        "anthropic:claude-haiku-4-5-20251001",
        output_type=ListingResults,
        instructions=SYSTEM_PROMPT,
    )


def parse_listings(markdown: str, product_query: str) -> list[ReverbListing]:
    agent = _get_agent()
    logger.info("Parsing listings with PydanticAI agent")
    prompt = (
        f"The user is searching for: '{product_query}'. "
        f"Extract all listings from this Reverb marketplace page. "
        f"Set is_primary_product to true ONLY if the listing is actually a '{product_query}' unit. "
        f"Any other product, even from the same brand, should be marked as is_primary_product=false.\n\n"
        f"{markdown}"
    )
    result = agent.run_sync(prompt)
    logger.info("Extracted %d listing(s)", len(result.output.listings))
    return result.output.listings


def filter_listings(listings: list[ReverbListing], watch: Watch) -> list[ReverbListing]:
    logger.debug("Filtering %d listings for watch '%s'", len(listings), watch.name)
    matches = []
    for listing in listings:
        if not listing.is_primary_product:
            logger.debug("Skipping accessory: %s", listing.title)
            continue

        if watch.exclude_terms:
            excluded = [term for term in watch.exclude_terms if re.search(rf"\b{re.escape(term)}\b", listing.title, re.IGNORECASE)]
            if excluded:
                logger.debug("Skipping excluded term %s: %s", excluded, listing.title)
                continue

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
