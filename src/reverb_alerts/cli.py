import logging
import os
from pathlib import Path

import click

from reverb_alerts.config import load_watches
from reverb_alerts.notify import create_alert
from reverb_alerts.parser import filter_listings, parse_listings
from reverb_alerts.scraper import scrape_reverb


def _setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    if not debug:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)


@click.command()
@click.option("--config", "config_path", default="./watches.yaml", type=click.Path(exists=True), help="Path to watches config file")
@click.option("--dry-run", "mode", flag_value="dry-run", help="Print matches without creating issues")
@click.option("--execute", "mode", flag_value="execute", help="Create GitHub issues for matches")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def main(config_path: str, mode: str | None, debug: bool) -> None:
    if not os.environ.get("CI"):
        from dotenv import load_dotenv
        load_dotenv()

    _setup_logging(debug)

    if mode is None:
        raise click.UsageError("Either --dry-run or --execute is required")

    watches = load_watches(Path(config_path))

    for watch in watches:
        click.echo(f"Checking: {watch.name} (max ${watch.max_price:.2f})...")

        markdown = scrape_reverb(watch.query, watch.max_price, watch.location, watch.conditions)
        listings = parse_listings(markdown)
        matches = filter_listings(listings, watch)

        if not matches:
            click.echo(f"  No matches found for {watch.name}")
            continue

        click.echo(f"  Found {len(matches)} match(es) for {watch.name}")

        if mode == "dry-run":
            for listing in matches:
                shipping = listing.shipping_cost or 0
                total = listing.price + shipping
                condition = listing.condition.value if listing.condition else "N/A"
                click.echo(f"    - {listing.title}: ${listing.price:.2f} + ${shipping:.2f} shipping = ${total:.2f} [{condition}]")
                click.echo(f"      {listing.url}")
        else:
            created = create_alert(watch.name, matches)
            if created:
                click.echo(f"  Created GitHub issue for {watch.name}")
            else:
                click.echo(f"  Skipped issue for {watch.name} (already exists or failed to create)")
