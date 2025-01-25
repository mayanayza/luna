from enum import Enum

#Default values for media folders + extensions
MEDIA = {
   'images': ("*.png","*.jpg","*.jpeg", "*.JPG", "*.JPEG"),
   'videos': ("*.mp4", "*.webm"),
   'models': ("*.glb", "*.mp4"),
   'audio': ("*.mp3", "*.wav"),
   'docs': ("*.pdf",)
}
      
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