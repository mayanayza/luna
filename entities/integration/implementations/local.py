import os
import shutil
from pathlib import Path

from common.constants import Files, Media
from entities.integration import Integration
from entities.project import Project


class LocalIntegration(Integration):
    """Integration that manages local project files and directories."""

    def __init__(self, registry, **kwargs):

        super().__init__(registry, **kwargs)

        self.config.update({
            'base_dir': kwargs.get('base_dir', str(Path.home())),
            'use_git': kwargs.get('use_git', True)
        })

    @property
    def base_dir(self) -> Path:
        """Get the base directory for all projects"""
        return Path(self.config['base_dir'] or str(Path.home()))

    def path(self, project) -> Path:
        return self.base_dir / project.name

    def setup(self, project: Project, **kwargs) -> None:
        """Set up local directory structure for a project"""

        # Create directory structure
        project_path = self.path(project)
        project_path.mkdir(parents=True, exist_ok=True)

        (project_path / 'src').mkdir(parents=True, exist_ok=True)
        (project_path / 'content').mkdir(parents=True, exist_ok=True)
        (project_path / 'media').mkdir(parents=True, exist_ok=True)
        (project_path / 'media-internal').mkdir(parents=True, exist_ok=True)
        
        # Create media directory structure
        for media in Media.ALL_TYPES:
            (project_path / 'media' / media.TYPE).mkdir(parents=True, exist_ok=True)
            (project_path / 'media-internal' / media.TYPE).mkdir(parents=True, exist_ok=True)

        # Create initial content files
        open(project_path / 'content/content.md', 'w').close()
        open(project_path / 'content/README.md', 'w').close()

        # Copy template files
        templates_dir = Path(os.getcwd()) / 'src' / 'script' / 'templates' / 'setup'
        if (templates_dir / Files.GITIGNORE).exists():
            shutil.copy(templates_dir / Files.GITIGNORE, project_path / Files.GITIGNORE)

    def remove(self, project: Project, **kwargs):
        """Remove local files for a project"""

        # Remove project directory
        project_path = self.path(project)
        if project_path.exists():
            shutil.rmtree(project_path)
        
        # Remove output directory if it exists
        output_dir = self.base_dir / '_output' / project.name
            
        if output_dir.exists():
            shutil.rmtree(output_dir)

    def rename(self, project: Project, old_name, **kwargs):
        """Rename local project directory"""
        try:                
            # Calculate paths
            old_dir = self.base_dir / old_name
            new_dir = self.base_dir / project.name
            
            if old_dir.exists():
                # Create parent directory if needed
                new_dir.parent.mkdir(parents=True, exist_ok=True)
                
                # Rename directory
                old_dir.rename(new_dir)
                self.logger.info(f"Renamed local directory from {old_dir} to {new_dir}")
            else:
                # Create the directories if they don't exist - this is a new approach
                self.logger.info(f"Directory {old_dir} not found, creating new one at {new_dir}")
                new_dir.mkdir(parents=True, exist_ok=True)
                
                # Set up the project filesystem
                self.setup(project)
        except Exception as e:
            self.logger.error(f"Error renaming local directory: {e}")

    def stage(self, project: Project, **kwargs):
        pass

    def publish(self, project: Project, **kwargs):
        """Publish project files to output directory"""
        project_dir = self.path(project)
        output_dir = self.base_dir / '_output' / project.name
        
        if output_dir.exists():
            shutil.rmtree(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)

        # Copy content files
        for content_file in [Files.README, Files.CONTENT]:
            source_path = project_dir / 'content' / content_file
            if source_path.exists():
                shutil.copy2(source_path, output_dir / content_file)

        # # Copy media files
        # for media in Media.ALL_TYPES:
        #     media_files = self.registry.service.get_media_files(project, media.TYPE)
        #     for file in media_files:
        #         shutil.copy2(file, output_dir / file.name)
    