"""Simple text-based parser for kupi.cz when CSS selectors don't work."""
import re
from typing import List, Dict, Any, Optional


def parse_kupi_offers_from_text(text: str) -> Dict[str, Any]:
    """
    Parse offers from raw text extracted from kupi.cz page.
    
    Args:
        text: Raw text content from the page
        
    Returns:
        Dictionary with product_name and offers list
    """
    result: Dict[str, Any] = {
        "product_name": None,
        "offers": []
    }
    
    # Extract product name
    title_match = re.search(r'Aktuální akční slevy ([^\n]+?) \d+\s*kg', text)
    if title_match:
        result["product_name"] = title_match.group(1).strip()
    
    # Pattern for each major Czech retailer
    retailers = ['Lidl', 'Penny Market', 'Kaufland', 'Tesco', 'Albert', 'BILLA', 'Billa']
    
    for retailer in retailers:
        # Find all occurrences of this retailer with offer data
        pattern = rf'{retailer}(\d+)\s*nejbližších\s*poboček.*?([\d,]+)\s*Kč\s*/\s*\d+\s*kg.*?–(\d+)\s*%.*?(platí[^PV]+|zítra[^PV]+|čt[^PV]+|pá[^PV]+)'
        
        for match in re.finditer(pattern, text, re.DOTALL):
            store_count = match.group(1)
            price = match.group(2)
            discount = match.group(3)
            validity_raw = match.group(4)
            
            # Clean validity text
            validity = re.sub(r'V\s*letáku.*', '', validity_raw).strip()
            validity = re.sub(r'Přidat.*', '', validity).strip()
            validity = validity[:50]  # Limit length
            
            offer = {
                "retailer_name": retailer,
                "store_count": int(store_count) if store_count else None,
                "price_text": f"{price} Kč / 1 kg",
                "price_value": float(price.replace(',', '.')) if price else None,
                "price_unit": "1 kg",
                "discount_percentage": int(discount) if discount else None,
                "validity_text": validity
            }
            
            # Avoid exact duplicates based on retailer + price
            is_dup = any(
                o["retailer_name"] == offer["retailer_name"] and 
                o["price_value"] == offer["price_value"]
                for o in result["offers"]
            )
            
            if not is_dup:
                result["offers"].append(offer)
    
    return result
