from enum import Enum

#Default values for media folders + extensions

class MediaProperties:
   def __init__(self, TYPE, EXTENSIONS):
      self.TYPE = TYPE
      self.EXT = EXTENSIONS

class Media:
   IMAGES = MediaProperties('images', ("*.png","*.jpg","*.jpeg", "*.JPG", "*.JPEG"))
   VIDEOS = MediaProperties('videos', ("*.mp4", "*.webm"))
   MODELS = MediaProperties('models', ("*.glb",))
   AUDIO = MediaProperties('audio', ("*.mp3", "*.wav"))
   DOCS = MediaProperties('docs', ("*.pdf",))
   EMBEDS = MediaProperties('embeds', ("*",))
      
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