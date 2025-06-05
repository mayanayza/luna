from enum import Enum

class ApplicationLayer(Enum):
    ENTITY = 'entity'
    REGISTRY = 'registry'
    SERVICE = 'service'
    CLI = 'cli'

class EntityType(Enum):
    PROJECT = 'project'
    INTEGRATION = 'integration'
    PROJECT_INTEGRATION = 'project_integration'
    DATABASE = 'database'

class CommandType(Enum):
    
    # General
    CREATE = 'create'
    RENAME = 'rename'
    DETAIL = 'detail'
    LIST = 'list'
    LIST_MODULES = 'list_modules'
    DELETE = 'delete'
    EDIT = 'edit'

    # Project
    ADD_INTEGRATION = 'add_integration'
    REMOVE_INTEGRATION = 'remove_integration'
    LIST_INTEGRATIONS = 'list_integrations'

    # Integration
    ADD_TO_PROJECT = 'add_to_project'

    # Project integration
    PUBLISH = 'publish'
    STAGE = 'stage'

    # Database
    CLEAR = 'clear'
    TEST = 'tests'