"""
Type helper functions for safe type conversions and handling SQLAlchemy types.
"""
from typing import Optional, Any, Union
from datetime import datetime
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy import Column


def as_float(v: Optional[Union[float, int, str, Column, ColumnElement]]) -> float:
    """Convert value to float safely, handling SQLAlchemy Column types."""
    if v is None:
        return 0.0
    if isinstance(v, (Column, ColumnElement)):
        # Cannot convert SQLAlchemy column directly to float
        # Return 0 as default for column objects
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def as_str(v: Optional[Union[str, Column, ColumnElement]]) -> str:
    """Convert value to string safely, handling SQLAlchemy Column types."""
    if v is None:
        return ""
    if isinstance(v, (Column, ColumnElement)):
        # Cannot convert SQLAlchemy column directly to string
        # Return empty string as default for column objects
        return ""
    return str(v)


def as_int(v: Optional[Union[int, str, float, Column, ColumnElement]]) -> int:
    """Convert value to int safely, handling SQLAlchemy Column types."""
    if v is None:
        return 0
    if isinstance(v, (Column, ColumnElement)):
        # Cannot convert SQLAlchemy column directly to int
        # Return 0 as default for column objects
        return 0
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def dt_iso(v: Optional[Union[datetime, Column, ColumnElement]]) -> Optional[str]:
    """Convert datetime to ISO string safely, handling SQLAlchemy Column types."""
    if v is None:
        return None
    if isinstance(v, (Column, ColumnElement)):
        # Cannot convert SQLAlchemy column directly
        return None
    if isinstance(v, datetime):
        return v.isoformat()
    return None


def safe_bool(v: Optional[Any]) -> bool:
    """Convert value to bool safely, handling SQLAlchemy Column types."""
    if v is None:
        return False
    if isinstance(v, (Column, ColumnElement)):
        # SQLAlchemy columns can't be used in boolean context directly
        # Always return False for column objects
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        return len(v) > 0
    return False


def safe_value(v: Any, default: Any = None) -> Any:
    """Extract value from SQLAlchemy column or return the value itself."""
    if v is None:
        return default
    if isinstance(v, (Column, ColumnElement)):
        # For column objects, we can't extract the value directly
        # Return the default value
        return default
    return v


def is_column(v: Any) -> bool:
    """Check if a value is a SQLAlchemy Column or ColumnElement."""
    return isinstance(v, (Column, ColumnElement))