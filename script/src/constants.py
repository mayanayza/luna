from enum import Enum

# Directory structure
MEDIA_TYPES = ['images', 'videos', 'models']

class Extensions:
   IMAGE = ("*.png","*.jpg","*.jpeg", "*.JPG", "*.JPEG")
   VIDEO = ("*.mp4", "*.webm")
   MODEL = ("*.glb",)
      
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