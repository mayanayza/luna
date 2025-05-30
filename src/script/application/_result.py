# simplified_result_system.py - Lightweight Result and Error System

from typing import Any, Dict, Generic, List, Optional, TypeVar

from src.script.application._error import Error, ErrorCategory

T = TypeVar('T')


class Result(Generic[T]):
    """Simple result wrapper"""
    
    def __init__(self, 
                 value: T = None, 
                 error: Error = None, 
                 errors: List[Error] = None):
        self._value = value
        self._errors = []
        
        if error:
            self._errors.append(error)
        if errors:
            self._errors.extend(errors)
    
    @property
    def is_success(self) -> bool:
        return len(self._errors) == 0
    
    @property
    def is_failure(self) -> bool:
        return not self.is_success
    
    @property
    def value(self) -> T:
        if self.is_failure:
            raise ValueError(f"Cannot get value from failed result: {self.error_message}")
        return self._value
    
    @property
    def errors(self) -> List[Error]:
        return self._errors.copy()
    
    @property
    def error(self) -> Optional[Error]:
        """Get the first/primary error"""
        return self._errors[0] if self._errors else None
    
    @property
    def error_message(self) -> str:
        """Get primary error message or empty string"""
        return self.error.message if self.error else ""
    
    def or_else(self, default: T) -> T:
        """Get value if success, return default if failure"""
        return self._value if self.is_success else default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization/API responses"""
        if self.is_success:
            return {
                "success": True,
                "data": self._value
            }
        else:
            return {
                "success": False,
                "error": self.error_message,
                "errors": [e.to_dict() for e in self._errors]
            }
    
    def __str__(self) -> str:
        if self.is_success:
            return f"Success({self._value})"
        else:
            return f"Failure({self.error_message})"

class Results:
    """Simple factory for creating results"""
    
    @staticmethod
    def success(value: T = None) -> Result[T]:
        """Create successful result"""
        return Result(value=value)
    
    @staticmethod
    def failure(message: str, 
               code: str = "error", 
               category: ErrorCategory = ErrorCategory.SYSTEM,
               field: str = None,
               source: str = None) -> Result:
        """Create failed result"""
        error = Error(
            code=code,
            message=message,
            category=category,
            field=field,
            source=source
        )
        return Result(error=error)
    
    @staticmethod
    def validation_error(field: str, message: str, code: str = "invalid") -> Result:
        """Create validation failure"""
        error = Error(
            code=code,
            message=message,
            category=ErrorCategory.VALIDATION,
            field=field
        )
        return Result(error=error)
    
    @staticmethod
    def not_found(resource: str, identifier: str = None) -> Result:
        """Create not found failure"""
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        
        error = Error(
            code="not_found",
            message=message,
            category=ErrorCategory.NOT_FOUND
        )
        return Result(error=error)
    
    @staticmethod
    def conflict(message: str) -> Result:
        """Create conflict failure"""
        error = Error(
            code="conflict",
            message=message,
            category=ErrorCategory.CONFLICT
        )
        return Result(error=error)
    
    @staticmethod
    def from_exception(e: Exception, source: str = None) -> Result:
        """Create failure from exception"""
        error = Error(
            code=e.__class__.__name__,
            message=str(e),
            category=ErrorCategory.SYSTEM,
            source=source
        )
        return Result(error=error)





