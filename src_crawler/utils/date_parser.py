"""Date parsing utilities for Czech date formats."""
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any


class CzechDateParser:
    """Parser for Czech date formats commonly found on kupi.cz"""
    
    # Czech month names
    MONTHS_CS = {
        'ledna': 1, 'leden': 1,
        'února': 2, 'únor': 2,
        'března': 3, 'březen': 3,
        'dubna': 4, 'duben': 4,
        'května': 5, 'květen': 5,
        'června': 6, 'červen': 6,
        'července': 7, 'červenec': 7,
        'srpna': 8, 'srpen': 8,
        'září': 9,
        'října': 10, 'říjen': 10,
        'listopadu': 11, 'listopad': 11,
        'prosince': 12, 'prosinec': 12
    }
    
    # Czech day names
    DAYS_CS = {
        'pondělí': 0, 'po': 0,
        'úterý': 1, 'út': 1,
        'středa': 2, 'st': 2, 'středy': 2,
        'čtvrtek': 3, 'čt': 3,
        'pátek': 4, 'pá': 4,
        'sobota': 5, 'so': 5, 'sobotu': 5,
        'neděle': 6, 'ne': 6, 'neděli': 6
    }
    
    # Relative date keywords
    RELATIVE_DATES = {
        'dnes': 0,
        'zítra': 1,
        'pozítří': 2,
        'včera': -1,
        'předevčírem': -2
    }
    
    def __init__(self, current_date: Optional[datetime] = None):
        """
        Initialize parser with optional current date (for testing).
        
        Args:
            current_date: Reference date for relative date calculations. Defaults to now.
        """
        self.current_date = current_date or datetime.now()
    
    def parse_date_range(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse date range from Czech text.
        
        Examples:
            "platí do středy 17. 12." -> (None, "2025-12-17")
            "čt 18. 12. – pá 19. 12." -> ("2025-12-18", "2025-12-19")
            "platí od 16. 12. do 22. 12." -> ("2025-12-16", "2025-12-22")
            "zítra končí" -> (None, tomorrow's date)
        
        Args:
            text: Text containing date information in Czech
            
        Returns:
            Tuple of (start_date, end_date) in ISO format (YYYY-MM-DD)
            Either date can be None if not found
        """
        if not text:
            return None, None
        
        text = text.lower().strip()
        
        # Check for relative dates
        for keyword, days_offset in self.RELATIVE_DATES.items():
            if keyword in text:
                date = self.current_date + timedelta(days=days_offset)
                if 'končí' in text or 'do' in text:
                    return None, date.strftime('%Y-%m-%d')
                return date.strftime('%Y-%m-%d'), None
        
        # Pattern: "dd. mm." or "dd. mm. yyyy"
        date_pattern = r'(\d{1,2})\.\s*(\d{1,2})\.(?:\s*(\d{4}))?'
        
        dates = []
        for match in re.finditer(date_pattern, text):
            day = int(match.group(1))
            month = int(match.group(2))
            year = int(match.group(3)) if match.group(3) else self.current_date.year
            
            # Handle year rollover (e.g., if current month is 12 and date month is 1)
            if month < self.current_date.month and self.current_date.month >= 11:
                year += 1
            
            try:
                date = datetime(year, month, day)
                dates.append(date.strftime('%Y-%m-%d'))
            except ValueError:
                continue
        
        # Determine start and end dates
        if len(dates) == 0:
            return None, None
        elif len(dates) == 1:
            # Single date - determine if it's start or end based on keywords
            if any(word in text for word in ['do', 'končí', 'platí do']):
                return None, dates[0]
            elif any(word in text for word in ['od', 'začíná', 'platí od']):
                return dates[0], None
            else:
                # If unclear, treat as end date
                return None, dates[0]
        else:
            # Multiple dates - first is start, last is end
            return dates[0], dates[-1]
    
    def parse_validity_text(self, text: str) -> Dict[str, Optional[str]]:
        """
        Parse validity text and return structured data.
        
        Args:
            text: Validity text like "platí do středy 17. 12."
            
        Returns:
            Dictionary with start_date, end_date, and original text
        """
        start_date, end_date = self.parse_date_range(text)
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'text': text.strip() if text else None
        }
    
    def extract_dates_from_offer(self, offer_text: str) -> dict:
        """
        Extract all date-related information from an offer text.
        
        Args:
            offer_text: Full text of an offer that might contain date information
            
        Returns:
            Dictionary with validity information
        """
        # Look for common validity patterns
        validity_patterns = [
            r'platí[^.]*?(\d{1,2}\.\s*\d{1,2}\.(?:\s*\d{4})?)',
            r'od\s+(\d{1,2}\.\s*\d{1,2}\.)\s+do\s+(\d{1,2}\.\s*\d{1,2}\.)',
            r'(zítra|dnes|pozítří)\s+(končí|platí)',
            r'(po|út|st|čt|pá|so|ne)\s+(\d{1,2}\.\s*\d{1,2}\.)',
        ]
        
        for pattern in validity_patterns:
            match = re.search(pattern, offer_text.lower())
            if match:
                return self.parse_validity_text(match.group(0))
        
        return {
            'start_date': None,
            'end_date': None,
            'text': None
        }
