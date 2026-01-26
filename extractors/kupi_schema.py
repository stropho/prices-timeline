"""Extraction schema for kupi.cz product pages."""
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from typing import Dict, Any


def get_kupi_schema() -> JsonCssExtractionStrategy:
    """
    Returns the extraction schema for kupi.cz product deal pages.
    
    This schema extracts:
    - Product information (name, category)
    - Regular price
    - List of promotional offers with:
      - Retailer information
      - Promotional pricing
      - Validity dates
      - Links to flyers and store locations
    """
    
    schema = {
        "name": "KupiCzProductDeals",
        "baseSelector": "body",
        "fields": [
            {
                "name": "product_name",
                "selector": "h1",
                "type": "text"
            },
            {
                "name": "category",
                "selector": "nav.breadcrumb a, .breadcrumb a",
                "type": "list",
                "fields": [
                    {
                        "name": "name",
                        "type": "text"
                    },
                    {
                        "name": "url",
                        "type": "attribute",
                        "attribute": "href"
                    }
                ]
            },
            {
                "name": "regular_price_text",
                "selector": "p:contains('běžně stojí'), div:contains('běžně stojí'), span:contains('běžně stojí')",
                "type": "text"
            },
            {
                "name": "offers",
                "selector": "article, .offer-card, .product-card, div[class*='offer']",
                "type": "list",
                "fields": [
                    {
                        "name": "retailer_name",
                        "selector": "h2, h3, .retailer-name, [class*='store'] a, a[href*='/letaky/']",
                        "type": "text"
                    },
                    {
                        "name": "retailer_url",
                        "selector": "a[href*='/letaky/']",
                        "type": "attribute",
                        "attribute": "href"
                    },
                    {
                        "name": "price_text",
                        "selector": ".price, [class*='price'], strong, b",
                        "type": "text"
                    },
                    {
                        "name": "discount_text",
                        "selector": "[class*='discount'], [class*='percent'], span:contains('%'), div:contains('%')",
                        "type": "text"
                    },
                    {
                        "name": "validity_text",
                        "selector": "p, div, span",
                        "type": "text"
                    },
                    {
                        "name": "flyer_url",
                        "selector": "a[href*='/letak/']",
                        "type": "attribute",
                        "attribute": "href"
                    },
                    {
                        "name": "store_locations_url",
                        "selector": "a[href*='/obchod/']",
                        "type": "attribute",
                        "attribute": "href"
                    },
                    {
                        "name": "store_count_text",
                        "selector": "span:contains('poboček'), p:contains('poboček'), div:contains('poboček')",
                        "type": "text"
                    },
                    {
                        "name": "full_text",
                        "type": "text"
                    }
                ]
            }
        ]
    }
    
    return JsonCssExtractionStrategy(schema, verbose=True)


def get_simple_kupi_schema() -> JsonCssExtractionStrategy:
    """
    Returns a simpler extraction schema that gets all text content from offers.
    Use this as a fallback if the detailed schema doesn't match the page structure.
    """
    
    schema = {
        "name": "KupiCzSimple",
        "baseSelector": "body",
        "fields": [
            {
                "name": "page_title",
                "selector": "h1",
                "type": "text"
            },
            {
                "name": "main_content",
                "selector": "main, #content, .content, body",
                "type": "text"
            }
        ]
    }
    
    return JsonCssExtractionStrategy(schema, verbose=True)
