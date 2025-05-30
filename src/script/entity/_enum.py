from enum import Enum


class EntityType(Enum):
    PROJECT = 'project'
    INTEGRATION = 'integration'
    PROJECT_INTEGRATION = 'project_integration'
    API = 'api'
    DB = 'database'
    HANDLER = 'handler'

class EntityQuantity(Enum):
    """Defines how many entities a handler can accept"""
    SINGLE = "single"              # Exactly one entity
    MULTIPLE = "multiple"          # One or more entities
    MULTIPLE_OPTIONAL = "multiple_optional"  # Zero or more entities

class HandlerType(Enum):
    SYSTEM = 'system'
    USER = 'user'