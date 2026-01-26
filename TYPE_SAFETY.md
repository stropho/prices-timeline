# Type Safety Guide

This project uses comprehensive type hints throughout the codebase, providing TypeScript-like type safety for Python.

## Overview

All modules are fully typed with:
- **Function signatures**: Parameter and return types
- **Class attributes**: Typed instance variables
- **Optional types**: Explicit nullable values with `Optional[T]`
- **Generic types**: `Dict[str, Any]`, `List[str]`, etc.
- **Pydantic models**: Runtime validation with `BaseModel`

## Type Checking Tools

### MyPy
Static type checker that validates types at development time.

```bash
# Check all files
mypy .

# Check specific file
mypy main.py

# Use the provided script
./check_types.sh
```

### Configuration
See `mypy.ini` for strict type checking configuration:
- `disallow_untyped_defs`: All functions must have type hints
- `no_implicit_optional`: Explicit Optional[] required
- `warn_return_any`: Warns on untyped returns
- `strict_equality`: Type-safe equality checks

## Pydantic Models

Located in `types.py`, these models provide:
1. **Runtime validation**: Data is validated when creating model instances
2. **Auto-completion**: IDEs can suggest fields
3. **Documentation**: Self-documenting data structures
4. **Serialization**: Easy JSON conversion

### Example Usage

```python
from types import Offer, RetailerInfo, PriceInfo

# Create typed offer
offer = Offer(
    retailer=RetailerInfo(name="Lidl", url="https://..."),
    pricing=PriceInfo(text="17,90 Kč", value=17.90, currency="CZK"),
    validity=ValidityInfo(start_date="2025-12-18", end_date="2025-12-19")
)

# ValidationError raised if data is invalid
# IDE provides auto-completion for all fields
```

## Module Type Coverage

### ✅ `utils/date_parser.py`
- All methods fully typed
- Optional returns explicit
- Dict types specified with keys

### ✅ `utils/storage.py`
- Path operations typed
- Optional returns for missing data
- List return types explicit

### ✅ `extractors/kupi_schema.py`
- Schema functions return JsonCssExtractionStrategy
- Type imports added

### ✅ `crawlers/kupi_crawler.py`
- Async functions properly typed
- Config objects typed
- Result dictionaries typed

### ✅ `main.py`
- DataProcessor methods fully typed
- Pydantic models integration ready
- Optional returns explicit

### ✅ `types.py`
- Complete Pydantic model definitions
- All data structures typed
- Runtime validation enabled

## Benefits

1. **Catch errors early**: Type errors detected before runtime
2. **Better IDE support**: Auto-completion, refactoring, go-to-definition
3. **Self-documenting**: Types serve as inline documentation
4. **Refactoring confidence**: Changes propagate through type system
5. **Runtime validation**: Pydantic catches invalid data at runtime

## Type Hints Examples

### Functions
```python
def parse_date(text: str, year: int = 2025) -> Optional[str]:
    """Returns ISO date string or None."""
    pass
```

### Classes
```python
class Crawler:
    def __init__(self, timeout: int = 60000) -> None:
        self.timeout: int = timeout
        self.results: List[Dict[str, Any]] = []
```

### Async Functions
```python
async def fetch_url(url: str) -> Dict[str, Any]:
    """Async function with typed return."""
    pass
```

### Complex Types
```python
from typing import Dict, List, Optional, Union

# Dictionary with string keys and any values
config: Dict[str, Any] = {"timeout": 5000}

# List of dictionaries
results: List[Dict[str, str]] = [{"name": "Item1"}]

# Optional (can be None)
price: Optional[float] = None

# Union (one of multiple types)
response: Union[str, Dict[str, Any]] = get_response()
```

## IDE Integration

### VS Code
Install Python extension and enable type checking:
```json
{
  "python.linting.mypyEnabled": true,
  "python.linting.enabled": true
}
```

### PyCharm
Type checking is built-in and automatically enabled.

## Best Practices

1. **Always annotate function parameters and returns**
2. **Use `Optional[T]` for nullable values** (never use `T | None` style)
3. **Prefer specific types over `Any`** when possible
4. **Use Pydantic models for complex data structures**
5. **Run mypy regularly** during development
6. **Fix type errors immediately** - they indicate real issues

## Common Patterns

### Optional with default
```python
def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    if path is None:
        path = "config.json"
    # ...
```

### Type narrowing
```python
def process(data: Optional[Dict[str, Any]]) -> str:
    if data is None:
        return "No data"
    # mypy knows data is Dict[str, Any] here
    return data["key"]
```

### Generic return types
```python
def get_items() -> List[Dict[str, str]]:
    return [{"name": "item1"}, {"name": "item2"}]
```
