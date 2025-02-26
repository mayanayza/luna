import shutil

from src.script.channels._channel import Channel
from src.script.config import Config
from src.script.constants import Media
from src.script.utils import get_project_media_files, get_project_path


class RawHandler(Channel):
    def __init__(self, config: Config):
        init = {
            'name': __name__,
            'class_name':self.__class__.__name__,
            'config': config
        }
            
        super().__init__(**init)
        
    def get_commands(self):
        """Return commands supported by Raw handler"""
        return {
            'publish': self.handle_publish,
        }
        
    def handle_publish(self, **kwargs):
        """Handle publish command for raw file exports"""
        projects = self.validate_projects(kwargs.get('projects', []))
        for name in projects:
            try:
                self.publish(name)
                self.logger.info(f"Published raw files for {name}")
            except Exception as e:
                self.logger.error(f"Failed to publish raw files for {name}: {e}")

    def publish(self, name: str) -> None:        
        try:
            self.delete(name)

            project_dir = get_project_path(self, name)
            output_dir = self.config.base_dir / '_output' / name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(project_dir / 'content/README.md', output_dir / 'README.md')
            shutil.copy2(project_dir / 'content/content.md', output_dir / 'content.md')

            for media in Media.ALL_TYPES:
                media_files = get_project_media_files(self, name, media.TYPE)
                for file in media_files:
                    shutil.copy2(file, str(output_dir / file.name))
                
            self.logger.info(f"Published raw content at {output_dir}")
        except Exception as e:
            self.logger.error(f"Error publishing raw: {e}")
            raise

    def delete(self, name: str) -> None:
        try:
            output_dir = self.config.base_dir / '_output' / name

            if output_dir.exists():
                shutil.rmtree(output_dir)
        except Exception as e:
            self.logger.error(f"Error deleting raw content: {e}")
            raise