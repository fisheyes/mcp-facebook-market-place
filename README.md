# Facebook Marketplace MCP Server

An MCP (Model Context Protocol) server that scrapes Facebook Marketplace listings. Built with FastMCP and Playwright for headless browser automation.

## Features

- Search Facebook Marketplace listings
- Filter by date (last N days)
- Filter by location
- Returns structured data: title, price, location, URL, and image
- AWS Bedrock AgentCore Runtime compatible
- Streamable HTTP transport for cloud deployments

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd facebook_market_place

# Install dependencies with uv
uv sync

# Install Playwright browser
uv run playwright install chromium
```

## Usage

### As MCP Server (AWS AgentCore compatible)

```bash
uv run python server.py
```

Server starts on `http://0.0.0.0:8000/mcp` with streamable HTTP transport.

### As CLI Tool

```bash
# Basic search
uv run python scraper.py "brewing fermenter"

# Filter to last 7 days
uv run python scraper.py "iphone 15" --days 7

# Output as JSON
uv run python scraper.py "laptop" --json

# Different location
uv run python scraper.py "bike" --location 123456789

# Debug mode (saves screenshot)
uv run python scraper.py "test" --debug
```

## MCP Tools

### `search_marketplace`

Search Facebook Marketplace for listings.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | Search term (e.g., "brewing fermenter") |
| `days` | integer | No | Only show listings from last N days (1, 7, 30) |
| `location_id` | string | No | Facebook location ID (default: `108339199186201` for UK) |

**Returns:**

```json
[
  {
    "listing_id": "1383886916015812",
    "title": "33L Bucket Brewing Fermenter",
    "price": "£10",
    "location": "London",
    "url": "https://www.facebook.com/marketplace/item/1383886916015812",
    "image_url": "https://..."
  }
]
```

### `get_listing_details`

Get full details for a specific listing, including description and condition.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `listing_id` | string | Yes | The listing ID from search results |

**Returns:**

```json
{
  "listing_id": "1564592031413917",
  "title": "Malt Miller 35ltr Brew Kettle",
  "price": "£95",
  "location": "Swindon, Wiltshire",
  "description": "Used but now upgrading my kit.",
  "condition": "Used – like new",
  "listed_date": "Listed 6 days ago in Swindon, Wiltshire",
  "url": "https://www.facebook.com/marketplace/item/1564592031413917"
}
```

## AWS Bedrock AgentCore Deployment

This server meets AWS Bedrock AgentCore Runtime requirements:

- Stateless streamable-HTTP transport
- Listens on `0.0.0.0:8000`
- MCP endpoint at `/mcp`

```bash
# Install AgentCore toolkit
pip install bedrock-agentcore-starter-toolkit

# Configure and deploy
agentcore configure
agentcore launch
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |

## Project Structure

```
facebook_market_place/
├── server.py      # MCP server (FastMCP)
├── scraper.py     # Core scraping logic (Playwright)
├── pyproject.toml # Project dependencies
└── README.md      # This file
```

## Dependencies

- Python 3.11+
- FastMCP 2.x
- Playwright
- BeautifulSoup4

## License

MIT License - See LICENSE file for details.

**Note**: This license covers the code only. Users remain responsible for complying with Facebook's Terms of Service and all applicable laws when using this software. The license does not grant permission to violate third-party terms of service or applicable regulations.

## Geographic Configuration

This server is configured with UK defaults:
- Default location ID: `108339199186201` (United Kingdom)
- Default locale: `en_GB`

You can override these settings by providing different location IDs for other regions.

## ⚠️ Important Legal Disclaimer

**THIS SOFTWARE IS FOR EDUCATIONAL AND RESEARCH PURPOSES ONLY.**

- This project is intended for learning about web scraping, MCP servers, and browser automation
- Users must comply with Facebook's Terms of Service and robots.txt
- Commercial use may violate Facebook's terms and applicable laws
- Users are solely responsible for ensuring lawful use in their jurisdiction
- The authors assume no liability for misuse of this software
- Always respect rate limits and implement appropriate delays between requests
- Consider using Facebook's official APIs for production applications

**By using this software, you acknowledge that you have read and understood these terms and agree to use it responsibly and in compliance with all applicable laws and terms of service.**

## Final Reminder

This project demonstrates web scraping techniques for educational purposes. Always prioritize ethical use, respect website terms of service, and consider official APIs for production applications. The maintainers are not responsible for any misuse of this software.
