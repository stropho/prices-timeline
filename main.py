"""Main entry point for the prices timeline crawler."""
import asyncio
import logging
import os
import sys
import re
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from pydantic import ValidationError
from crawlers.kupi_crawler import KupiCrawler, load_urls_from_file
from utils.storage import StorageManager
from utils.date_parser import CzechDateParser
from types import (
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
        logging.FileHandler('crawler.log')
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
        
        result = {
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
                pass
        
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
        
        result = {
            "text": discount_text,
            "percentage": None
        }
        
        # Extract numeric value
        match = re.search(r'(\d+)\s*%', discount_text)
        if match:
            result["percentage"] = int(match.group(1))
        
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
        if not crawl_result.get("success") or not crawl_result.get("extracted_data"):
            return None
        
        extracted = crawl_result["extracted_data"]
        
        # Handle list format from JsonCssExtractionStrategy
        if isinstance(extracted, list) and len(extracted) > 0:
            extracted = extracted[0]
        
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
                    processed["offers"].append(processed_offer)
        
        return processed


async def main() -> None:
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("Starting Prices Timeline Crawler")
    logger.info("=" * 60)
    
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
    urls_file = 'config/urls.txt'
    urls = load_urls_from_file(urls_file)
    
    if not urls:
        logger.error(f"No URLs found in {urls_file}. Please add URLs to crawl.")
        return
    
    logger.info(f"Found {len(urls)} URLs to crawl")
    
    # Crawl URLs
    logger.info("Starting crawl...")
    results = await crawler.crawl_urls(urls, use_simple_schema=False, delay_between=True)
    
    # Process and save results
    logger.info("Processing and saving results...")
    success_count = 0
    error_count = 0
    
    for result in results:
        url = result["url"]
        
        if result["success"]:
            # Save raw data
            raw_path = storage.save_raw(
                url=url,
                data=result["extracted_data"],
                metadata={
                    "success": True,
                    "has_markdown": result["raw_markdown"] is not None
                }
            )
            logger.info(f"✓ Saved raw data: {raw_path}")
            
            # Process and save
            processed_data = processor.process_crawl_result(result)
            if processed_data:
                processed_path = storage.save_processed(url=url, data=processed_data)
                logger.info(f"✓ Saved processed data: {processed_path}")
                
                # Log summary
                offer_count = len(processed_data.get("offers", []))
                product_name = processed_data.get("product", {}).get("name", "Unknown")
                logger.info(f"  → Product: {product_name}, Offers: {offer_count}")
            else:
                logger.warning(f"⚠ Could not process data for {url}")
            
            success_count += 1
        else:
            error_msg = result.get("error", "Unknown error")
            logger.error(f"✗ Failed to crawl {url}: {error_msg}")
            
            # Save error information
            storage.save_raw(
                url=url,
                data={"error": error_msg},
                metadata={"success": False}
            )
            error_count += 1
    
    # Summary
    logger.info("=" * 60)
    logger.info(f"Crawl completed!")
    logger.info(f"Success: {success_count}/{len(urls)}")
    logger.info(f"Errors: {error_count}/{len(urls)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
