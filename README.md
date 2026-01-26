# Prices Timeline Crawler

A web crawler built with crawl4ai to extract promotional product deals from kupi.cz and save structured data to JSON files.

## Features

- Crawls specific product pages from kupi.cz (Czech deals aggregator)
- Extracts promotional offers with pricing, retailers, validity dates
- Handles JavaScript-rendered content using Playwright
- Parses Czech date formats
- Saves raw and processed data to JSON files
- Always fetches fresh data (no caching)

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run crawl4ai setup (required for Playwright/browser):**
   ```bash
   crawl4ai-setup
   ```

3. **Verify installation:**
   ```bash
   crawl4ai-doctor
   ```

4. **Configure URLs:**
   Edit `config/urls.txt` and add target URLs (one per line)

5. **Optional: Create .env file:**
   ```bash
   cp .env.example .env
   ```

## Type Checking

This project uses comprehensive type hints (similar to TypeScript) for better code safety and IDE support.

**Run type checking:**
```bash
mypy .
```

All modules are fully typed with:
- Function parameter and return type annotations
- Optional types for nullable values
- Generic types (Dict, List, etc.)
- Strict mypy configuration

## Usage

Run the crawler:
```bash
python main.py
```

## Project Structure

```
prices-timeline/
├── crawlers/           # Crawler implementations
├── extractors/         # Extraction schemas
├── config/             # Configuration files
│   └── urls.txt       # Target URLs to crawl
├── data/
│   ├── raw/           # Raw crawl results
│   └── processed/     # Processed JSON files
├── utils/             # Helper utilities
├── main.py            # Entry point
└── requirements.txt   # Python dependencies
```

## Output

- **Raw data:** `data/raw/{product_slug}_{timestamp}.json`
- **Processed data:** `data/processed/{product_slug}_latest.json`

## Data Structure

Extracted data includes:
- Product name and category
- Regular price
- Promotional offers:
  - Retailer name and links
  - Promotional price and discount percentage
  - Validity dates (start/end)
  - Flyer and store location URLs
  - Store count

## Notes

- The crawler uses a 2-second delay between requests for polite crawling
- JavaScript rendering is enabled to capture dynamic content
- Czech locale headers are set for proper content
- All dates are converted to ISO format (YYYY-MM-DD)
