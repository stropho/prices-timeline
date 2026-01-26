"""Type definitions and Pydantic models for structured data."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl


class RetailerInfo(BaseModel):
    """Information about a retailer."""
    name: Optional[str] = None
    url: Optional[str] = None


class PriceInfo(BaseModel):
    """Price information with parsed values."""
    text: str
    value: Optional[float] = None
    currency: Optional[str] = None
    unit: Optional[str] = None


class DiscountInfo(BaseModel):
    """Discount information."""
    text: str
    percentage: Optional[int] = None


class ValidityInfo(BaseModel):
    """Validity period information."""
    start_date: Optional[str] = Field(None, description="ISO format date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="ISO format date (YYYY-MM-DD)")
    text: Optional[str] = None


class StoreLocationsInfo(BaseModel):
    """Store location information."""
    url: Optional[str] = None
    count: Optional[int] = None


class Offer(BaseModel):
    """A promotional offer from a retailer."""
    retailer: RetailerInfo
    pricing: Optional[PriceInfo] = None
    discount: Optional[DiscountInfo] = None
    validity: ValidityInfo
    flyer_url: Optional[str] = None
    store_locations: StoreLocationsInfo
    raw_text: Optional[str] = None


class CategoryInfo(BaseModel):
    """Category breadcrumb information."""
    name: str
    url: Optional[str] = None


class ProductInfo(BaseModel):
    """Product information."""
    name: Optional[str] = None
    category: List[CategoryInfo] = Field(default_factory=list)
    regular_price: Optional[PriceInfo] = None


class CrawlMetadata(BaseModel):
    """Metadata about the crawl operation."""
    url: str
    crawled_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    slug: Optional[str] = None
    success: bool = True


class ProcessedData(BaseModel):
    """Complete processed data structure."""
    product: ProductInfo
    offers: List[Offer] = Field(default_factory=list)
    metadata: CrawlMetadata


class CrawlResult(BaseModel):
    """Result from a crawl operation."""
    success: bool
    url: str
    extracted_data: Optional[dict] = None
    raw_markdown: Optional[str] = None
    error: Optional[str] = None
