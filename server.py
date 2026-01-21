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

from scraper import scrape_marketplace_async, get_listing_details_async

mcp = FastMCP("Facebook Marketplace")


@mcp.tool()
async def search_marketplace(
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
    listings = await scrape_marketplace_async(
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


@mcp.tool()
async def get_listing_details(listing_id: str) -> dict:
    """
    Get full details for a specific Facebook Marketplace listing.

    Use this to get the complete description, condition, and other details
    for a listing found via search_marketplace.

    Args:
        listing_id: The listing ID (from search_marketplace results or URL)

    Returns:
        Full listing details including description, condition, and listing date.
    """
    details = await get_listing_details_async(listing_id=listing_id, headless=True)

    return {
        "listing_id": details.listing_id,
        "title": details.title,
        "price": details.price,
        "location": details.location,
        "description": details.description,
        "condition": details.condition,
        "listed_date": details.listed_date,
        "url": details.url,
    }


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
        stateless_http=True,
    )
