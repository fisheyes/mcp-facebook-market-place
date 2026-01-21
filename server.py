#!/usr/bin/env python3
"""
Facebook Marketplace MCP Server

Exposes Facebook Marketplace scraping functionality via MCP protocol.
Configured for AWS Bedrock AgentCore Runtime compatibility.

Requirements:
- Stateless streamable-HTTP transport
- Listens on 0.0.0.0:8000
- MCP endpoint at /mcp
"""

from typing import Optional

from fastmcp import FastMCP

from scraper import scrape_marketplace

mcp = FastMCP("Facebook Marketplace")


@mcp.tool()
def search_marketplace(
    query: str,
    days: Optional[int] = None,
    location_id: str = "108339199186201",
) -> list[dict]:
    """
    Search Facebook Marketplace for listings.

    Args:
        query: Search term (e.g., "brewing fermenter", "iphone 15")
        days: Only show listings from the last N days (e.g., 1, 7, 30). If not specified, shows all.
        location_id: Facebook location ID. Default is a UK location.

    Returns:
        List of marketplace listings with title, price, location, url, and image_url.
    """
    listings = scrape_marketplace(
        query=query,
        location_id=location_id,
        days_listed=days,
        headless=True,
    )

    return [
        {
            "listing_id": l.listing_id,
            "title": l.title,
            "price": l.price,
            "location": l.location,
            "url": l.url,
            "image_url": l.image_url,
        }
        for l in listings
    ]


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
        stateless_http=True,
    )
