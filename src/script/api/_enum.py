from enum import Enum


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

    # Project integration
    PUBLISH = 'publish'
    STAGE = 'stage'

    # Database
    CLEAR = 'clear'