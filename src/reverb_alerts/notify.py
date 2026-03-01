import json
import logging
import subprocess

from reverb_alerts.models import ReverbListing

logger = logging.getLogger(__name__)


def _issue_exists(title: str) -> bool:
    result = subprocess.run(
        ["gh", "issue", "list", "--state", "open", "--search", f'"{title}" in:title', "--json", "title"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.debug("gh issue list failed: %s", result.stderr)
        return False

    issues = json.loads(result.stdout)
    return any(issue["title"] == title for issue in issues)


def _ensure_label(label: str) -> None:
    subprocess.run(
        ["gh", "label", "create", label, "--color", "0E8A16", "--force"],
        capture_output=True,
        text=True,
    )


def _format_issue_body(listings: list[ReverbListing]) -> str:
    lines = [
        "| Title | Price | Shipping | Total | Condition | Location | Link |",
        "|-------|-------|----------|-------|-----------|----------|------|",
    ]
    for listing in listings:
        shipping = f"${listing.shipping_cost:.2f}" if listing.shipping_cost else "Free"
        total_cost = listing.price + (listing.shipping_cost or 0)
        condition = listing.condition.value if listing.condition else "N/A"
        location = listing.seller_location or "N/A"
        lines.append(
            f"| {listing.title} | ${listing.price:.2f} | {shipping} "
            f"| ${total_cost:.2f} | {condition} | {location} "
            f"| [View]({listing.url}) |"
        )
    return "\n".join(lines)


def create_alert(watch_name: str, listings: list[ReverbListing]) -> bool:
    title = f"Deal Alert: {watch_name}"

    if _issue_exists(title):
        logger.info("Open issue already exists: %s", title)
        return False

    _ensure_label("deal-alert")
    body = _format_issue_body(listings)

    result = subprocess.run(
        [
            "gh", "issue", "create",
            "--title", title,
            "--body", body,
            "--label", "deal-alert",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("Failed to create issue: %s", result.stderr)
    return result.returncode == 0
