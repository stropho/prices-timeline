"""Main entry point for the prices timeline crawler."""
import asyncio
import logging
import os
import sys
import re
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to Python path for imports
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from crawlers.kupi_crawler import KupiCrawler, load_urls_from_file, SchemaMode
from utils.storage import StorageManager
from utils.date_parser import CzechDateParser
from utils.text_parser import parse_kupi_offers_from_text
from models import (
    Offer, RetailerInfo, PriceInfo, DiscountInfo, 
    ValidityInfo, StoreLocationsInfo, ProcessedData
)


# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(__file__).parent.parent / 'crawler.log')
    ]
)
logger = logging.getLogger(__name__)


class DataProcessor:
    """Process and clean extracted data."""
    
    def __init__(self) -> None:
        self.date_parser = CzechDateParser()
    
    def _parse_price(self, price_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse price text to extract numeric value and unit.
        
        Args:
            price_text: Text like "17,90 Kč / 1 kg" or "40,76 Kč"
            
        Returns:
            Dictionary with value, currency, and unit
        """
        if not price_text:
            return None
        
        result: Dict[str, Any] = {
            "text": price_text,
            "value": None,
            "currency": None,
            "unit": None
        }
        
        # Extract numeric value (Czech uses comma as decimal separator)
        price_match = re.search(r'(\d+[,.]?\d*)', price_text)
        if price_match:
            value_str = price_match.group(1).replace(',', '.')
            try:
                result["value"] = float(value_str)
            except ValueError:
                result["value"] = None
        
        # Extract currency
        if 'Kč' in price_text or 'CZK' in price_text:
            result["currency"] = "CZK"
        
        # Extract unit (e.g., "/ 1 kg", "/ ks")
        unit_match = re.search(r'/\s*(.+?)(?:\s|$)', price_text)
        if unit_match:
            result["unit"] = unit_match.group(1).strip()
        
        return result
    
    def _parse_discount(self, discount_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse discount text to extract percentage.
        
        Args:
            discount_text: Text like "–55 %" or "55%"
            
        Returns:
            Dictionary with percentage value
        """
        if not discount_text:
            return None
        
        result: Dict[str, Any] = {
            "text": discount_text,
            "percentage": None
        }
        
        # Extract numeric value
        match = re.search(r'(\d+)\s*%', discount_text)
        if match:
            result["percentage"] = int(match.group(1))
        else:
            result["percentage"] = None
        
        return result
    
    def _parse_store_count(self, store_count_text: str) -> Optional[int]:
        """
        Parse store count from text.
        
        Args:
            store_count_text: Text like "81 nejbližších poboček"
            
        Returns:
            Integer count or None
        """
        if not store_count_text:
            return None
        
        match = re.search(r'(\d+)', store_count_text)
        if match:
            return int(match.group(1))
        
        return None
    
    def process_offer(self, offer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single offer to extract structured data.
        
        Args:
            offer: Raw offer data from extraction
            
        Returns:
            Processed offer with structured fields
        """
        processed = {
            "retailer": {
                "name": offer.get("retailer_name", "").strip() if offer.get("retailer_name") else None,
                "url": offer.get("retailer_url")
            },
            "pricing": self._parse_price(offer.get("price_text", "")),
            "discount": self._parse_discount(offer.get("discount_text", "")),
            "validity": self.date_parser.parse_validity_text(offer.get("validity_text", "")),
            "flyer_url": offer.get("flyer_url"),
            "store_locations": {
                "url": offer.get("store_locations_url"),
                "count": self._parse_store_count(offer.get("store_count_text", ""))
            },
            "raw_text": offer.get("full_text", "").strip() if offer.get("full_text") else None
        }
        
        return processed
    
    def process_crawl_result(self, crawl_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process complete crawl result.
        
        Args:
            crawl_result: Raw crawl result from crawler
            
        Returns:
            Processed data structure
        """
        if not crawl_result.get("success"):
            return None
        
        # Try to parse from raw text if CSS extraction failed
        extracted = crawl_result.get("extracted_data")
        if extracted:
            # Handle list format from JsonCssExtractionStrategy
            if isinstance(extracted, list) and len(extracted) > 0:
                extracted = extracted[0]
            
            # Check if we got meaningful offer data
            offers = extracted.get("offers", [])
            if not offers or len(offers) == 0:
                # Fallback to text parsing
                logger.info("CSS extraction found no offers, trying text parser...")
                raw_text = extracted.get("regular_price_text", "")
                if raw_text:
                    parsed = parse_kupi_offers_from_text(raw_text)
                    if parsed.get("offers"):
                        logger.info(f"Text parser found {len(parsed['offers'])} offers")
                        # Create fake extracted structure from parsed text
                        extracted = {
                            "product_name": parsed.get("product_name", extracted.get("product_name")),
                            "category": extracted.get("category", []),
                            "regular_price_text": extracted.get("regular_price_text"),
                            "offers": parsed.get("offers", [])
                        }
        else:
            return None
        
        processed = {
            "product": {
                "name": extracted.get("product_name", "").strip() if extracted.get("product_name") else None,
                "category": extracted.get("category", []),
                "regular_price": self._parse_price(extracted.get("regular_price_text", ""))
            },
            "offers": [],
            "metadata": {
                "url": crawl_result.get("url"),
                "crawled_at": datetime.now().isoformat()
            }
        }
        
        # Process offers
        offers = extracted.get("offers", [])
        if offers:
            for offer in offers:
                processed_offer = self.process_offer(offer)
                # Only include offers with at least a retailer name or price
                if processed_offer["retailer"]["name"] or processed_offer["pricing"]:
                    if isinstance(processed["offers"], list):
                        processed["offers"].append(processed_offer)
        
        return processed


async def main() -> None:
    # ...existing code for crawl, results, combined_data...


    # Initialize components
    crawler_delay = int(os.getenv('CRAWLER_DELAY_SECONDS', '2'))
    crawler_timeout = int(os.getenv('CRAWLER_TIMEOUT_MS', '60000'))
    crawler_headless = os.getenv('CRAWLER_HEADLESS', 'true').lower() == 'true'

    crawler = KupiCrawler(
        headless=crawler_headless,
        delay_seconds=crawler_delay,
        timeout_ms=crawler_timeout
    )
    storage = StorageManager()
    processor = DataProcessor()

    # Load URLs
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    urls_file = script_dir / 'config' / 'urls.txt'
    urls = load_urls_from_file(str(urls_file))

    if not urls:
        logger.error(f"No URLs found in {urls_file}. Please add URLs to crawl.")
        return

    logger.info(f"Found {len(urls)} URLs to crawl")

    # Crawl URLs
    logger.info("Starting crawl...")
    results = await crawler.crawl_urls(urls, schema_mode=SchemaMode.LLM, delay_between=True)

    # Write markdown files and build combined_data in a single loop
    markdown_dir = storage.raw_dir / "markdown"
    markdown_dir.mkdir(parents=True, exist_ok=True)
    combined_data = []
    for i, result in enumerate(results):
        url = result.get("url", "")
        slug = storage._extract_slug_from_url(url) if url else f"entry_{i+1}"
        filename = f"{slug}.md"
        md_path = markdown_dir / filename
        markdown_content = result.get("raw_markdown") or ""
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        entry = {
            "slug": slug,
            "url": url,
            "markdown": markdown_content,
            "extracted_data": result.get("extracted_data")
        }
        combined_data.append(entry)
    logger.info(f"✓ Saved markdown files to: {markdown_dir}")
    # Write combined_data.json
    combined_path = storage.raw_dir / "combined_data.json"
    import json
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)
    logger.info(f"✓ Aggregated {len(combined_data)} entries into: {combined_path}")
    logger.info("=" * 60)
    logger.info("Crawl completed! Markdown files saved and combined_data.json created.")
    logger.info(f"Success: {sum(1 for r in results if r.get('success'))}/{len(urls)}")
    logger.info(f"Errors: {sum(1 for r in results if not r.get('success'))}/{len(urls)}")
    logger.info("=" * 60)
    
    # ...existing code for initialization, crawling, and processing...


if __name__ == "__main__":
    asyncio.run(main())
