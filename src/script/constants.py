from enum import Enum


class EntityType:
    PROJECT = 'project'
    INTEGRATION = 'integration'
    PROJECT_INTEGRATION = 'project_integration'
    API = 'api'
    DB = 'database'
    HANDLER = 'handler'

class Command:
    CREATE = 'create'
    RENAME = 'rename'
    ADD_INTEGRATION = 'add_integration'
    REMOVE_INTEGRATION = 'remove_integration'
    LIST = 'list'
    DELETE = 'delete'
    EDIT = 'edit'


class MediaProperties:
   def __init__(self, TYPE, EXTENSIONS):
      self.TYPE = TYPE
      self.EXT = EXTENSIONS

class MediaPropertiesCollector(type):
    def __new__(cls, name, bases, attrs):
        # Create the class
        new_cls = super().__new__(cls, name, bases, attrs)
        
        # Collect all MediaProperties instances
        new_cls.ALL_TYPES = [
            value for value in attrs.values() 
            if isinstance(value, MediaProperties)
        ]
        
        return new_cls

class Media(metaclass=MediaPropertiesCollector):
    IMAGES = MediaProperties('images', ("*.png","*.jpg","*.jpeg", "*.JPG", "*.JPEG"))
    VIDEOS = MediaProperties('videos', ("*.mov","*.mp4"))
    MODELS = MediaProperties('models', ("*.stl",))
    AUDIO = MediaProperties('audio', ("*.mp3", "*.wav"))
    DOCS = MediaProperties('docs', ("*.pdf",))
    EMBEDS = MediaProperties('embeds', ("*",))

    @classmethod
    def get_extensions(cls, media_type: str) -> tuple:
        """Get extensions for a specific media type"""
        return next(t.EXT for t in cls.ALL_TYPES if t.TYPE == media_type)
      
# Template file names
class Files:
   README = 'README.md'
   METADATA = 'metadata.yml'
   CONTENT = 'content.md'
   GITIGNORE = '.gitignore'

# Status enums
class Status(str, Enum):
   ARCHIVE = 'archive'
   BACKLOG = 'backlog'
   IN_PROGRESS = 'in_progress'
   COMPLETE = 'complete'