from enum import Enum

# Directory structure
BASE_DIRS = ['src', 'docs', 'hardware'] 
MEDIA_TYPES = ['images', 'videos', 'models']

class Extensions:
   IMAGE = ("*.png","*.jpg","*.jpeg", "*.JPG", "*.JPEG")
   VIDEO = (".mp4", "*.webm")
   MODEL = ("*.glb")

# Template file names
class Files:
   README = 'README.md'
   METADATA = 'metadata.yml'
   CONTENT = 'content.md'
   GITIGNORE = '.gitignore'
   PDF_LAYOUT = 'pdf_layout.html'
   PDF_STYLE = 'pdf_style.css'

# Status enums
class Status(str, Enum):
   ARCHIVE = 'archive'
   BACKLOG = 'backlog'
   IN_PROGRESS = 'in_progress'
   COMPLETE = 'complete'