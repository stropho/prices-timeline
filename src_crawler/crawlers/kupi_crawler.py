"""Crawler implementation for kupi.cz."""
import asyncio
import logging
import os
from typing import Dict, Any, List, Optional, Union
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from extractors.kupi_schema import get_kupi_schema, get_simple_kupi_schema, get_llm_instruction
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
        if schema_mode == SchemaMode.LLM:
            # Crawl without extraction strategy; call litellm directly after to avoid
            # crawl4ai's chunking + <blocks> XML prompt which breaks Groq JSON mode.
            css_selector_str = os.getenv("LLM_CSS_SELECTOR", "")
            # CrawlerRunConfig css_selector uses comma-separated selectors
            css_selector = ", ".join(s.strip() for s in css_selector_str.split("|") if s.strip()) or None
            run_config = CrawlerRunConfig(
                cache_mode=self.default_run_config.cache_mode,
                page_timeout=self.default_run_config.page_timeout,
                wait_until=self.default_run_config.wait_until,
                css_selector=css_selector,
                verbose=True
            )
            logger.info(f"LLM mode: crawling with css_selector={css_selector!r}")
        elif schema_mode == SchemaMode.SIMPLE:
            extraction_strategy = get_simple_kupi_schema()
            logger.info("Using simple extraction schema")
            run_config = CrawlerRunConfig(
                cache_mode=self.default_run_config.cache_mode,
                page_timeout=self.default_run_config.page_timeout,
                wait_until=self.default_run_config.wait_until,
                extraction_strategy=extraction_strategy,
                verbose=True
            )
        else:
            extraction_strategy = get_kupi_schema()
            logger.info("Using detailed extraction schema")
            run_config = CrawlerRunConfig(
                cache_mode=self.default_run_config.cache_mode,
                page_timeout=self.default_run_config.page_timeout,
                wait_until=self.default_run_config.wait_until,
                extraction_strategy=extraction_strategy,
                verbose=True
            )
        
        result_data = {
            "success": False,
            "url": url,
            "extracted_data": None,
            "raw_markdown": None,
            "token_usage": None,
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
                    markdown = result.markdown.raw_markdown if result.markdown else ""
                    result_data["raw_markdown"] = markdown
                    result_data["success"] = True

                    if schema_mode == SchemaMode.LLM:
                        try:
                            extracted_data, token_usage = await self._extract_with_llm(markdown, url)
                            result_data["extracted_data"] = extracted_data
                            result_data["token_usage"] = token_usage
                        except Exception as llm_err:
                            logger.error(f"LLM extraction failed for {url}: {llm_err}")
                            result_data["extracted_data"] = [{"error": True, "content": str(llm_err)}]
                    else:
                        import json
                        extracted_data = None
                        if result.extracted_content:
                            try:
                                extracted_data = json.loads(result.extracted_content)
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to parse extracted content: {e}")
                                extracted_data = {"raw": result.extracted_content}
                        result_data["extracted_data"] = extracted_data

                else:
                    logger.error(f"Crawl failed for {url}: {result.error_message}")
                    result_data["error"] = result.error_message
                    
        except Exception as e:
            logger.error(f"Exception while crawling {url}: {str(e)}")
            result_data["error"] = str(e)
        
        return result_data

    async def _extract_with_llm(self, markdown: str, url: str):
        """Call litellm directly on the full markdown — no chunking, no XML wrapper."""
        import json
        from litellm import acompletion
        instruction = get_llm_instruction()
        provider = os.getenv("LLM_PROVIDER")
        api_key = os.getenv("LLM_API_KEY")
        if not markdown.strip():
            logger.warning(f"Empty markdown for {url} — check LLM_CSS_SELECTOR")
        logger.info(f"Calling LLM ({provider}) with {len(markdown)} chars of markdown")
        response = await acompletion(
            model=provider,
            messages=[
                {"role": "system", "content": "You are a data extraction assistant. Always return valid JSON."},
                {"role": "user", "content": f"{instruction}\n\nPage content:\n{markdown}"},
            ],
            api_key=api_key,
            response_format={"type": "json_object"},
            temperature=0.01,
        )
        content = response.choices[0].message.content
        logger.info(f"LLM raw response (first 200 chars): {content[:200]}")
        extracted = json.loads(content)
        # Wrap in list so downstream processing (which expects a list) stays unchanged
        extracted_data = [extracted] if isinstance(extracted, dict) else extracted
        token_usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
        logger.info(
            f"Token usage for {url}: "
            f"prompt={token_usage['prompt_tokens']}, "
            f"completion={token_usage['completion_tokens']}, "
            f"total={token_usage['total_tokens']}"
        )
        return extracted_data, token_usage

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
        
        if schema_mode == SchemaMode.LLM:
            total_prompt = sum(r["token_usage"]["prompt_tokens"] for r in results if r.get("token_usage"))
            total_completion = sum(r["token_usage"]["completion_tokens"] for r in results if r.get("token_usage"))
            total_tokens = sum(r["token_usage"]["total_tokens"] for r in results if r.get("token_usage"))
            logger.info(
                f"Total token usage across {len(urls)} URLs: "
                f"prompt={total_prompt}, completion={total_completion}, total={total_tokens}"
            )
        
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
