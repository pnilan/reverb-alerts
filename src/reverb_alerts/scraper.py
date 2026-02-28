import os
from urllib.parse import quote

from firecrawl import FirecrawlApp


def scrape_reverb(query: str, location: str | None = None) -> str | None:
    app = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])

    url = f"https://reverb.com/marketplace?query={quote(query)}&sort=price%7Casc"
    if location:
        url += f"&item_region={quote(location)}"

    result = app.scrape(url, formats=["markdown"])

    return result.markdown
