from datetime import datetime

import yaml

from script.src.config import Config
from script.src.constants import BASE_DIRS, MEDIA_TYPES, Files
from script.src.utils import (
    get_media_path,
    get_project_metadata,
    get_project_path,
    load_template,
    setup_logging,
)


class SetupHandler:

    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logging(__name__)

    def create(self, name: str, display_name: str) -> None:
        """Create the project directory structure and initialize files"""
        
        project_dir = get_project_path(self, name)

        for base_dir in BASE_DIRS:
            (project_dir / base_dir).mkdir(parents=True, exist_ok=True)

        # Create media directory structure
        for media_type in MEDIA_TYPES:
            get_media_path(self, project_dir, media_type).mkdir(parents=True, exist_ok=True)
            get_media_path(self, project_dir, media_type, internal=True).mkdir(parents=True, exist_ok=True)

        # Load and process templates
        date = datetime.now().strftime('%Y-%m-%d')
        template_vars = {
            'display_name': display_name,
            'name': name,
            'date': date
        }

        # Create content.md from template
        content_template = load_template(self, Files.CONTENT)
        with open(project_dir / Files.CONTENT, 'w') as f:
            f.write(content_template)

        # Create metadata.yml from template
        metadata_content = load_template(self, Files.METADATA).format(**template_vars)
        with open(project_dir / Files.METADATA, 'w') as f:
            f.write(metadata_content)

        # Create .gitignore from template
        gitignore_content = load_template(self, Files.GITIGNORE)
        with open(project_dir / Files.GITIGNORE, 'w') as f:
            f.write(gitignore_content)

    def rename(self, old_name: str, old_display_name: str, old_path: str, new_name: str, new_display_name: str, new_path: str) -> None:
        # Update metadata
        metadata = get_project_metadata(self, old_name)
        metadata['project']['name'] = new_name
        metadata['project']['display_name'] = new_display_name
        
        # Save updated metadata
        with open(old_path / Files.METADATA, 'w') as f:
            yaml.safe_dump(metadata, f, sort_keys=False, allow_unicode=True)
        
        # Rename local directory
        old_path.rename(new_path)