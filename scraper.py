#!/usr/bin/env python3
"""
Facebook Marketplace Scraper

Uses Playwright to scrape listing data from Facebook Marketplace search results.
Runs headless by default. Supports both sync and async APIs.

IMPORTANT: This scraper is for educational purposes only. Users must:
- Comply with Facebook's Terms of Service
- Respect rate limits and implement appropriate delays
- Use for research/educational purposes only
- Not use for commercial data harvesting

Default delays are implemented to encourage responsible usage.
"""

import asyncio
import json
import re
import sys
from dataclasses import dataclass, asdict
from typing import Optional
from urllib.parse import quote

from playwright.async_api import async_playwright, Page as AsyncPage
from playwright.sync_api import sync_playwright, Page as SyncPage


@dataclass
class MarketplaceListing:
    """Data model for a Facebook Marketplace listing."""
    listing_id: str
    title: str
    price: str
    location: str
    url: str
    image_url: Optional[str] = None


@dataclass
class ListingDetails:
    """Full details for a single Facebook Marketplace listing."""
    listing_id: str
    title: str
    price: str
    location: str
    description: str
    condition: Optional[str] = None
    listed_date: Optional[str] = None
    seller_name: Optional[str] = None
    url: Optional[str] = None


def _parse_listing_text(all_text: str) -> tuple[str, str, str]:
    """Parse listing text to extract title, price, and location."""
    title = ''
    price = ''
    location = ''

    lines = [line.strip() for line in all_text.split('\n') if line.strip()]

    for line in lines:
        # Price detection (£, $, €, or "Free")
        if re.match(r'^[\$£€][\d,\.]+', line) or re.match(r'^[\d,\.]+\s*[\$£€]', line) or line.lower() == 'free':
            if not price:
                price = line
        elif not title and len(line) > 2 and not re.match(r'^\d+$', line):
            title = line
        elif title and not location and len(line) > 2:
            location = line

    return title, price, location


async def extract_listings_from_page_async(page: AsyncPage) -> list[MarketplaceListing]:
    """Extract listing data from the rendered page (async version)."""
    listings = []
    seen_ids = set()

    await page.wait_for_selector('a[href*="/marketplace/item/"]', timeout=15000)
    listing_links = await page.query_selector_all('a[href*="/marketplace/item/"]')

    for link in listing_links:
        href = await link.get_attribute('href') or ''
        match = re.search(r'/marketplace/item/(\d+)', href)
        if not match:
            continue

        listing_id = match.group(1)
        if listing_id in seen_ids:
            continue
        seen_ids.add(listing_id)

        all_text = (await link.inner_text()).strip()
        title, price, location = _parse_listing_text(all_text)

        image_url = None
        img = await link.query_selector('img')
        if img:
            image_url = await img.get_attribute('src')

        if title or price:
            listings.append(MarketplaceListing(
                listing_id=listing_id,
                title=title or f"Listing {listing_id}",
                price=price or "Price not listed",
                location=location,
                url=f"https://www.facebook.com/marketplace/item/{listing_id}",
                image_url=image_url,
            ))

    return listings


def extract_listings_from_page_sync(page: SyncPage) -> list[MarketplaceListing]:
    """Extract listing data from the rendered page (sync version)."""
    listings = []
    seen_ids = set()

    page.wait_for_selector('a[href*="/marketplace/item/"]', timeout=15000)
    listing_links = page.query_selector_all('a[href*="/marketplace/item/"]')

    for link in listing_links:
        href = link.get_attribute('href') or ''
        match = re.search(r'/marketplace/item/(\d+)', href)
        if not match:
            continue

        listing_id = match.group(1)
        if listing_id in seen_ids:
            continue
        seen_ids.add(listing_id)

        all_text = link.inner_text().strip()
        title, price, location = _parse_listing_text(all_text)

        image_url = None
        img = link.query_selector('img')
        if img:
            image_url = img.get_attribute('src')

        if title or price:
            listings.append(MarketplaceListing(
                listing_id=listing_id,
                title=title or f"Listing {listing_id}",
                price=price or "Price not listed",
                location=location,
                url=f"https://www.facebook.com/marketplace/item/{listing_id}",
                image_url=image_url,
            ))

    return listings


def _build_url(query: str, location_id: str, locale: str, days_listed: Optional[int]) -> str:
    """Build the marketplace search URL."""
    encoded_query = quote(query)
    url = f"https://www.facebook.com/marketplace/{location_id}/search?query={encoded_query}&locale={locale}"
    if days_listed is not None:
        url += f"&daysSinceListed={days_listed}"
    return url


async def scrape_marketplace_async(
    query: str,
    location_id: str = "108339199186201",
    locale: str = "en_GB",
    days_listed: Optional[int] = None,
    headless: bool = True,
) -> list[MarketplaceListing]:
    """
    Scrape Facebook Marketplace search results (async version).

    Use this when calling from an async context (e.g., MCP server).
    """
    url = _build_url(query, location_id, locale, days_listed)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until='networkidle', timeout=30000)

            # Handle cookie consent
            try:
                cookie_btn = await page.query_selector('button[data-cookiebanner="accept_button"]')
                if cookie_btn:
                    await cookie_btn.click()
                    await page.wait_for_timeout(1000)
            except Exception:
                pass

            try:
                cookie_btn = await page.query_selector('button:has-text("Allow all cookies")')
                if cookie_btn:
                    await cookie_btn.click()
                    await page.wait_for_timeout(1000)
            except Exception:
                pass

            # Wait for content to load
            await page.wait_for_timeout(2000)

            # Respectful delay before scraping (minimum 3 seconds)
            # This helps respect Facebook's servers and reduces load
            await page.wait_for_timeout(3000)

            listings = await extract_listings_from_page_async(page)

        finally:
            await browser.close()

    return listings


async def get_listing_details_async(
    listing_id: str,
    headless: bool = True,
) -> ListingDetails:
    """
    Get full details for a specific listing (async version).

    Args:
        listing_id: The Facebook Marketplace listing ID
        headless: Run browser in headless mode

    Returns:
        ListingDetails with full description and metadata
    """
    url = f"https://www.facebook.com/marketplace/item/{listing_id}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until='networkidle', timeout=30000)

            # Handle cookie consent
            try:
                cookie_btn = await page.query_selector('button[data-cookiebanner="accept_button"]')
                if cookie_btn:
                    await cookie_btn.click()
                    await page.wait_for_timeout(1000)
            except Exception:
                pass

            try:
                cookie_btn = await page.query_selector('button:has-text("Allow all cookies")')
                if cookie_btn:
                    await cookie_btn.click()
                    await page.wait_for_timeout(1000)
            except Exception:
                pass

            await page.wait_for_timeout(2000)

            # Respectful delay before scraping (minimum 3 seconds)
            # This helps respect Facebook's servers and reduces load
            await page.wait_for_timeout(3000)

            # Get all text from the page
            body_text = await page.inner_text('body')
            lines = [line.strip() for line in body_text.split('\n') if line.strip()]

            # Parse the listing details
            title = ''
            price = ''
            location = ''
            description = ''
            condition = None
            listed_date = None

            # Find key markers in the text
            for i, line in enumerate(lines):
                # Price is usually a line starting with currency
                if re.match(r'^[\$£€][\d,\.]+$', line) or line.lower() == 'free':
                    if not price:
                        price = line

                # "Listed X days ago" or "Listed on..."
                if line.startswith('Listed ') and ('ago' in line or 'in ' in line):
                    listed_date = line

                # Condition markers
                if line.startswith('Condition'):
                    # Next non-empty line is usually the condition value
                    if i + 1 < len(lines):
                        condition = lines[i + 1]

                # Location marker
                if 'Location is approximate' in line and i > 0:
                    # Location is usually a few lines before this
                    for j in range(i - 1, max(0, i - 5), -1):
                        if lines[j] and not lines[j].startswith('Listed') and len(lines[j]) > 3:
                            location = lines[j]
                            break

            # Find title - usually appears early and matches listing title pattern
            # It often appears after "Details" section
            details_idx = None
            for i, line in enumerate(lines):
                if line == 'Details':
                    details_idx = i
                    break

            if details_idx:
                # Look for title and description after Details
                # Pattern: Details -> Condition -> [condition value] -> [title] -> [description lines]
                found_condition = False
                past_condition = False
                desc_lines = []
                for i in range(details_idx + 1, min(details_idx + 20, len(lines))):
                    line = lines[i]
                    if line == 'Condition':
                        found_condition = True
                        continue
                    if found_condition and not past_condition:
                        condition = line
                        past_condition = True
                        continue
                    if line in ['Message', 'Save', 'Share', 'Location is approximate']:
                        break
                    if past_condition and not title and len(line) > 5 and not re.match(r'^[\$£€]', line):
                        title = line
                    elif title and line != title and len(line) > 2 and line != condition:
                        desc_lines.append(line)

                description = '\n'.join(desc_lines)

            # Fallback: if no title found, use first substantial text
            if not title:
                for line in lines:
                    if len(line) > 10 and not re.match(r'^[\$£€]', line) and 'Facebook' not in line:
                        title = line
                        break

            return ListingDetails(
                listing_id=listing_id,
                title=title,
                price=price,
                location=location,
                description=description,
                condition=condition,
                listed_date=listed_date,
                url=url,
            )

        finally:
            await browser.close()


def scrape_marketplace(
    query: str,
    location_id: str = "108339199186201",
    locale: str = "en_GB",
    days_listed: Optional[int] = None,
    headless: bool = True,
    debug: bool = False,
) -> list[MarketplaceListing]:
    """
    Scrape Facebook Marketplace search results (sync version).

    Use this for CLI usage or non-async contexts.
    """
    url = _build_url(query, location_id, locale, days_listed)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until='networkidle', timeout=30000)

            # Handle cookie consent
            try:
                cookie_btn = page.query_selector('button[data-cookiebanner="accept_button"]')
                if cookie_btn:
                    cookie_btn.click()
                    page.wait_for_timeout(1000)
            except Exception:
                pass

            try:
                cookie_btn = page.query_selector('button:has-text("Allow all cookies")')
                if cookie_btn:
                    cookie_btn.click()
                    page.wait_for_timeout(1000)
            except Exception:
                pass

            page.wait_for_timeout(2000)

            # Respectful delay before scraping (minimum 3 seconds)
            # This helps respect Facebook's servers and reduces load
            page.wait_for_timeout(3000)

            if debug:
                page.screenshot(path='debug_screenshot.png')
                with open('debug_page.html', 'w') as f:
                    f.write(page.content())
                print("Debug files saved: debug_screenshot.png, debug_page.html")

            listings = extract_listings_from_page_sync(page)

        except Exception as e:
            if debug:
                page.screenshot(path='error_screenshot.png')
                with open('error_page.html', 'w') as f:
                    f.write(page.content())
                print(f"Error files saved: error_screenshot.png, error_page.html")
            raise e

        finally:
            browser.close()

    return listings


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Scrape Facebook Marketplace')
    parser.add_argument('query', nargs='?', default='brewing fermenter', help='Search query')
    parser.add_argument('--location', default='108339199186201', help='Facebook location ID')
    parser.add_argument('--days', type=int, help='Only show listings from the last N days (e.g., 1, 7, 30)')
    parser.add_argument('--debug', action='store_true', help='Save debug screenshot and HTML')
    parser.add_argument('--no-headless', action='store_true', help='Show browser window')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    print(f"Searching for: {args.query}")
    print("-" * 50)

    try:
        listings = scrape_marketplace(
            query=args.query,
            location_id=args.location,
            days_listed=args.days,
            headless=not args.no_headless,
            debug=args.debug,
        )

        if not listings:
            print("No listings found. Use --debug to save screenshot for inspection.")
            return

        if args.json:
            print(json.dumps([asdict(l) for l in listings], indent=2))
        else:
            for listing in listings:
                print(f"\nTitle: {listing.title}")
                print(f"Price: {listing.price}")
                print(f"Location: {listing.location}")
                print(f"URL: {listing.url}")

            print(f"\n{'-' * 50}")
            print(f"Found {len(listings)} listings")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
