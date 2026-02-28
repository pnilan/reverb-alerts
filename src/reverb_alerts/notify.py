import subprocess

from reverb_alerts.models import ReverbListing


def _issue_exists(title: str) -> bool:
    result = subprocess.run(
        ["gh", "issue", "list", "--state", "open", "--search", title, "--json", "title"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False

    import json

    issues = json.loads(result.stdout)
    return any(issue["title"] == title for issue in issues)


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
        return False

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
    return result.returncode == 0
