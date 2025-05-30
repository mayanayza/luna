from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class ErrorCategory(Enum):
    VALIDATION = "validation"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    SYSTEM = "system"
    BUSINESS = "business"


@dataclass
class Error:
    code: str
    message: str
    category: ErrorCategory = ErrorCategory.SYSTEM
    field: Optional[str] = None
    source: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "category": self.category.value,
            "field": self.field,
            "source": self.source
        }
