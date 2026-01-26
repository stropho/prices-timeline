"""Storage utilities for saving crawl results to JSON files."""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List
import re


class StorageManager:
    """Manages saving crawl results to JSON files."""
    
    def __init__(self, raw_dir: str = "data/raw", processed_dir: str = "data/processed"):
        """
        Initialize storage manager.
        
        Args:
            raw_dir: Directory for raw crawl results
            processed_dir: Directory for processed/cleaned results
        """
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        
        # Ensure directories exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def _extract_slug_from_url(self, url: str) -> str:
        """
        Extract product slug from URL.
        
        Args:
            url: Full URL like "https://www.kupi.cz/sleva/banany"
            
        Returns:
            Slug like "banany"
        """
        # Extract the last part of the path
        match = re.search(r'/sleva/([^/?#]+)', url)
        if match:
            return match.group(1)
        
        # Fallback: use last path segment
        path_parts = url.rstrip('/').split('/')
        return path_parts[-1] if path_parts else "unknown"
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to remove invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for filesystem
        """
        # Replace invalid characters with underscores
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove any remaining problematic characters
        sanitized = re.sub(r'[^\w\-.]', '_', sanitized)
        return sanitized
    
    def save_raw(self, url: str, data: Dict[str, Any], metadata: Dict[str, Any] = None) -> str:
        """
        Save raw crawl result with timestamp.
        
        Args:
            url: Source URL
            data: Crawl result data
            metadata: Optional metadata (timestamp, success status, etc.)
            
        Returns:
            Path to saved file
        """
        slug = self._extract_slug_from_url(url)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{slug}_{timestamp}.json"
        filepath = self.raw_dir / filename
        
        output = {
            "metadata": {
                "url": url,
                "scraped_at": datetime.now().isoformat(),
                "slug": slug,
                **(metadata or {})
            },
            "data": data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def save_processed(self, url: str, data: Dict[str, Any]) -> str:
        """
        Save processed result (overwrites previous version).
        
        Args:
            url: Source URL
            data: Processed data
            
        Returns:
            Path to saved file
        """
        slug = self._extract_slug_from_url(url)
        filename = f"{slug}_latest.json"
        filepath = self.processed_dir / filename
        
        output = {
            "metadata": {
                "url": url,
                "processed_at": datetime.now().isoformat(),
                "slug": slug
            },
            "data": data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def load_processed(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Load processed data for a given slug.
        
        Args:
            slug: Product slug
            
        Returns:
            Processed data dictionary or None if not found
        """
        filename = f"{slug}_latest.json"
        filepath = self.processed_dir / filename
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_raw_files(self, slug: Optional[str] = None) -> List[str]:
        """
        List raw data files, optionally filtered by slug.
        
        Args:
            slug: Optional product slug to filter by
            
        Returns:
            List of file paths
        """
        if slug:
            pattern = f"{slug}_*.json"
        else:
            pattern = "*.json"
        
        return sorted([str(f) for f in self.raw_dir.glob(pattern)])
    
    def list_processed_files(self) -> List[str]:
        """
        List all processed data files.
        
        Returns:
            List of file paths
        """
        return sorted([str(f) for f in self.processed_dir.glob("*_latest.json")])
