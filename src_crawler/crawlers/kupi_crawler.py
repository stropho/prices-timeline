"""Crawler implementation for kupi.cz."""
import asyncio
import logging
import os
from typing import Dict, Any, List, Optional, Union
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from extractors.kupi_schema import get_kupi_schema, get_simple_kupi_schema, get_kupi_schema_llm
from enum import Enum

class SchemaMode(Enum):
    DETAILED = "detailed"
    SIMPLE = "simple"
    LLM = "llm"


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KupiCrawler:
    """Crawler for kupi.cz product deal pages."""
    
    def __init__(
        self,
        headless: bool = True,
        delay_seconds: int = 2,
        timeout_ms: int = 60000
    ) -> None:
        """
        Initialize the crawler.
        
        Args:
            headless: Run browser in headless mode
            delay_seconds: Delay between requests (polite crawling)
            timeout_ms: Page load timeout in milliseconds
        """
        self.headless = headless
        self.delay_seconds = delay_seconds
        self.timeout_ms = timeout_ms
        
        # Browser configuration with headers
        self.browser_config = BrowserConfig(
            headless=self.headless,
            viewport_width=1280,
            viewport_height=720,
            browser_type="chromium",
            verbose=False,
            extra_args=["--lang=cs-CZ"]
        )
        
        # Default crawl configuration
        self.default_run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,  # Always get fresh data
            page_timeout=self.timeout_ms,
            wait_until="domcontentloaded",  # Wait for DOM to load (faster than networkidle)
            delay_before_return_html=2.0,  # Wait 2 seconds for JS to render
            verbose=False
        )
    
    async def crawl_url(
        self,
        url: str,
        schema_mode: "SchemaMode" = SchemaMode.DETAILED
    ) -> Dict[str, Any]:
        """
        Crawl a single URL and extract structured data.
        
        Args:
            url: URL to crawl
            use_simple_schema: Use simple fallback schema if True
            
        Returns:
            Dictionary containing:
                - success: bool
                - url: str
                - extracted_data: dict (parsed from JSON)
                - raw_markdown: str
                - error: str (if failed)
        """
        logger.info(f"Crawling URL: {url}")
        
        # Choose extraction schema
        target_elements: Optional[List[str]] = None
        if schema_mode == SchemaMode.LLM:
            # Get target elements from environment (pipe-delimited list of CSS selectors)
            css_selector_str = os.getenv("LLM_CSS_SELECTOR")
            if css_selector_str:
                target_elements = [selector.strip() for selector in css_selector_str.split("|") if selector.strip()]
            extraction_strategy = get_kupi_schema_llm()
            if target_elements:
                logger.info(f"Using LLM extraction schema with target elements: {target_elements}")
            else:
                logger.info("Using LLM extraction schema without target element filtering")
        elif schema_mode == SchemaMode.SIMPLE:
            extraction_strategy = get_simple_kupi_schema()
            logger.info("Using simple extraction schema")
        else:
            extraction_strategy = get_kupi_schema()
            logger.info("Using detailed extraction schema")
        
        # Update run config with extraction strategy and target elements
        # The target_elements parameter filters HTML before processing, reducing LLM token usage
        run_config = CrawlerRunConfig(
            cache_mode=self.default_run_config.cache_mode,
            page_timeout=self.default_run_config.page_timeout,
            wait_until=self.default_run_config.wait_until,
            extraction_strategy=extraction_strategy,
            target_elements=target_elements,  # Filter HTML before LLM processing
            verbose=True
        )
        
        result_data = {
            "success": False,
            "url": url,
            "extracted_data": None,
            "raw_markdown": None,
            "error": None
        }
        
        try:
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                result = await crawler.arun(
                    url=url,
                    config=run_config
                )
                
                if result.success:
                    logger.info(f"Successfully crawled: {url}")
                    
                    # Parse extracted content
                    extracted_data = None
                    if result.extracted_content:
                        try:
                            import json
                            extracted_data = json.loads(result.extracted_content)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse extracted content: {e}")
                            extracted_data = {"raw": result.extracted_content}
                    
                    result_data["success"] = True
                    result_data["extracted_data"] = extracted_data
                    result_data["raw_markdown"] = result.markdown.raw_markdown if result.markdown else None
                    
                else:
                    logger.error(f"Crawl failed for {url}: {result.error_message}")
                    result_data["error"] = result.error_message
                    
        except Exception as e:
            logger.error(f"Exception while crawling {url}: {str(e)}")
            result_data["error"] = str(e)
        
        return result_data
    
    async def crawl_urls(
        self,
        urls: List[str],
        schema_mode: "SchemaMode" = SchemaMode.DETAILED,
        delay_between: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Crawl multiple URLs sequentially.
        
        Args:
            urls: List of URLs to crawl
            use_simple_schema: Use simple fallback schema if True
            delay_between: Add delay between requests
            
        Returns:
            List of result dictionaries
        """
        results = []
        
        for i, url in enumerate(urls):
            logger.info(f"Processing URL {i+1}/{len(urls)}")
            result = await self.crawl_url(url, schema_mode=schema_mode)
            results.append(result)
            # Polite crawling: delay between requests
            if delay_between and i < len(urls) - 1:
                logger.info(f"Waiting {self.delay_seconds} seconds before next request...")
                await asyncio.sleep(self.delay_seconds)
        
        return results
    
    async def crawl_urls_parallel(
        self,
        urls: List[str],
        schema_mode: "SchemaMode" = SchemaMode.DETAILED,
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Crawl multiple URLs in parallel with concurrency limit.
        
        Args:
            urls: List of URLs to crawl
            use_simple_schema: Use simple fallback schema
            max_concurrent: Maximum number of concurrent requests
            
        Returns:
            List of result dictionaries
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def crawl_with_semaphore(url: str) -> Dict[str, Any]:
            async with semaphore:
                return await self.crawl_url(url, schema_mode=schema_mode)

        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks)

        return list(results)


def load_urls_from_file(filepath: str) -> List[str]:
    """
    Load URLs from a text file (one URL per line).
    
    Args:
        filepath: Path to file containing URLs
        
    Returns:
        List of URLs (comments and empty lines ignored)
    """
    urls: list[str] = []
    
    if not os.path.exists(filepath):
        logger.warning(f"URLs file not found: {filepath}")
        return urls
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                urls.append(line)
    
    logger.info(f"Loaded {len(urls)} URLs from {filepath}")
    return urls
