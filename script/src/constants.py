from enum import Enum

# Directory structure
BASE_DIRS = ['src', 'docs', 'hardware'] 
MEDIA_TYPES = ['images', 'videos', 'models']

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