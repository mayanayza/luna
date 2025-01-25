import shutil
from datetime import datetime

import yaml

from script.src.config import Config
from script.src.constants import MEDIA_TYPES, Files
from script.src.utils import (
    get_project_metadata,
    get_project_path,
    load_template,
    setup_logging,
)


class FileHandler:

    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logging(__name__)

    def create(self, name: str, display_name: str, title: str) -> None:
        """Create the project directory structure and initialize files"""
        try:
            project_dir = get_project_path(self, name)
            (project_dir / 'src').mkdir(parents=True, exist_ok=True)
            (project_dir / 'content').mkdir(parents=True, exist_ok=True)
            (project_dir / 'media').mkdir(parents=True, exist_ok=True)
            (project_dir / 'media-internal').mkdir(parents=True, exist_ok=True)

            # Create media directory structure
            for media_type in MEDIA_TYPES:
                (project_dir / 'media' / media_type).mkdir(parents=True, exist_ok=True)
                (project_dir / 'media-internal' / media_type).mkdir(parents=True, exist_ok=True)

            # Load and process templates
            date = datetime.now().strftime('%Y-%m-%d')
            template_vars = {
                'display_name': display_name,
                'name': name,
                'title': title,
                'date': date
            }

            # Create content.md from template
            content_template = load_template(self, Files.CONTENT)
            with open(project_dir / 'content' / Files.CONTENT, 'w') as f:
                f.write(content_template)

            # Create content.md from template
            readme_remplate = load_template(self, Files.README)
            with open(project_dir / 'content' / Files.README, 'w') as f:
                f.write(readme_remplate)

            # Create metadata.yml from template
            metadata_content = load_template(self, Files.METADATA).format(**template_vars)
            with open(project_dir / Files.METADATA, 'w') as f:
                f.write(metadata_content)

            # Create .gitignore from template
            gitignore_content = load_template(self, Files.GITIGNORE)
            with open(project_dir / Files.GITIGNORE, 'w') as f:
                f.write(gitignore_content)

            self.logger.info(f"Created project files for {name}")
        except Exception as e:
            self.logger.error(f"Failed to create project files for {name}: {e}")

    def rename(self, old_name: str, new_name: str, new_display_name: str, new_title: str) -> None:
        # Update metadata
        try:
            metadata = get_project_metadata(self, old_name)
            metadata['project']['name'] = new_name
            metadata['project']['display_name'] = new_display_name
            metadata['project']['title'] = new_title

            old_project_dir = get_project_path(self, old_name)
            new_project_dir = get_project_path(self, new_name)
            
            # Save updated metadata
            with open(old_project_dir / Files.METADATA, 'w') as f:
                yaml.safe_dump(metadata, f, sort_keys=False, allow_unicode=True)
            
            # Rename local directory
            old_project_dir.rename(new_project_dir)
            self.logger.info(f"Renamed project files from {old_name} to {new_name}")
        except Exception as e:
            self.logger.error(f"Failed to rename project files for {old_name}: {e}")

    def delete(self, name: str) -> None:
        try:
            
            project_dir = get_project_path(self, name)
            shutil.rmtree(project_dir)
            self.logger.info(f"Deleted project files for {name}")
        except Exception as e:
            self.logger.error(f"Failed to delete project files for {name}: {e}")
