import os
import shutil
from pathlib import Path
from typing import List

from src.script.common.constants import Files, Media
from src.script.entity.integration import Integration
from src.script.entity.project import Project
from src.script.input.input import InputField
from src.script.input.validation import InputValidator


class LocalIntegration(Integration):
    """Integration that manages local project files and directories."""

    def __init__(self, registry, **kwargs):

        super().__init__(registry, **kwargs)

        self._config_fields: List = [
            InputField(
                name='base_dir',
                title='Base Directory', 
                description='Directory where project folders will be created',
                default_value=str(Path.home()),
                field_type=str,
                validation_rules=[InputValidator.local_path_exists()]
            ),
            InputField(
                name='use_git',
                title='Use Github',
                description='Whether to initialize a github repo in project folders. Requires GitHub integration.',
                default_value=True,
                field_type=bool
            )
        ]

        self._project_integration_config_fields: List = []

    @property
    def base_dir(self) -> Path:
        """Get the base directory for all projects."""
        return Path(self.get_config_value('base_dir'))

    def path(self, project) -> Path:
        return self.base_dir / project.name

     ######                                ##
       ##                                  ##
       ##     ## ###   ######   ##   ##  ######    #####
       ##     ###  ##  ##   ##  ##   ##    ##     ##
       ##     ##   ##  ##   ##  ##   ##    ##      ####
       ##     ##   ##  ##   ##  ##  ###    ##         ##
     ######   ##   ##  ######    ### ##     ###   #####
                       ##

    @classmethod
    def get_publish_inputs(cls, entity, handler_registry, registry, **kwargs):
        return None

    @classmethod
    def get_stage_inputs(cls, entity, handler_registry, registry, **kwargs):
        return None

     ##   ##                         ##   ###
     ##   ##                         ##    ##
     ##   ##   ######  ## ###    ######    ##      #####   ## ###    #####
     #######  ##   ##  ###  ##  ##   ##    ##     ##   ##  ###      ##
     ##   ##  ##   ##  ##   ##  ##   ##    ##     #######  ##        ####
     ##   ##  ##  ###  ##   ##  ##   ##    ##     ##       ##           ##
     ##   ##   ### ##  ##   ##   ######   ####     #####   ##       #####

    @classmethod
    def handle_edit(cls, entity, base_dir, use_git, **kwargs):
        entity.logger.debug(f"{base_dir.old} -> {base_dir.new}")
        entity.logger.debug(f"{use_git.old} -> {use_git.new}")

        # if not Path(new_value).exists():
        #     self.logger.info(f"Creating directory: {new_value}")
        #     Path(new_value).mkdir(parents=True, exist_ok=True)

    @classmethod
    def handle_publish(cls, entity, project: Project, **kwargs):
        """
        Publish project files to output directory.
        
        Args:
            project_ref: Reference to the project
            **kwargs: Additional parameters
            
        Returns:
            dict: Result of the operation
        """

        # Create output directory
        project_dir = entity.path(project)
        output_dir = entity.base_dir / '_output' / project.name
        
        if output_dir.exists():
            shutil.rmtree(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)

        # Copy content files
        for content_file in [Files.README, Files.CONTENT]:
            source_path = project_dir / 'content' / content_file
            if source_path.exists():
                shutil.copy2(source_path, output_dir / content_file)

        # Copy media files
        for media in Media.ALL_TYPES:
            media_files = entity.get_media_files(project, media.TYPE)
            for file in media_files:
                shutil.copy2(file, output_dir / file.name)

    @classmethod
    def handle_stage(cls, entity, project: Project, **kwargs):
        pass
    

    def get_readme(self, project: Project) -> str:
        """
        Get the project README file content.
        
        Args:
            project: Project instance
            
        Returns:
            str: README content
        """
        project_path = self.path(project)
        readme_path = project_path / 'content' / Files.README
        if readme_path.exists():
            with open(readme_path, 'r') as f:
                return f.read()
        return ""

    def get_content(self, project: Project) -> str:
        """
        Get the project content file.
        
        Args:
            project: Project instance
            
        Returns:
            str: Content file content
        """
        project_path = self.path(project)
        content_path = project_path / 'content' / Files.CONTENT
        if content_path.exists():
            with open(content_path, 'r') as f:
                return f.read()
        return ""

    def get_media_files(self, project: Project, media_type):
        """
        Get media files of a specific type.
        
        Args:
            project: Project instance
            media_type: Type of media to get
            
        Returns:
            list: List of media file paths
        """
        project_path = self.path(project)
        media_path = project_path / 'media' / media_type
        extensions = Media.get_extensions(media_type)
        files = []
        if media_path.exists():
            for ext in extensions:
                files.extend(list(media_path.glob(ext)))
        return files

    def setup(self, project: Project, **kwargs) -> None:
        """
        Set up the local integration for a project.
        
        Args:
            project_ref: Reference to the project
            **kwargs: Additional parameters
        """
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
        """
        Remove local files for a project.
        
        Args:
            project_ref: Reference to the project
            **kwargs: Additional parameters
            
        Returns:
            dict: Result of the operation
        """

        # Remove project directory
        project_path = self.path(project)
        if project_path.exists():
            shutil.rmtree(project_path)
        
        # Remove output directory if it exists
        output_dir = self.base_dir / '_output' / project.name
            
        if output_dir.exists():
            shutil.rmtree(output_dir)

    # def handle_save_project(self, project: Project, data, **kwargs):
    #     """
    #     Save project data to disk.
        
    #     Args:
    #         project_ref: Reference to the project
    #         data: Project data to save
    #         **kwargs: Additional parameters
            
    #     Returns:
    #         dict: Result of the operation
    #     """
    #     # Get project from reference
        
    #     try:
    #         # Save project data to YAML file
    #         import yaml
    #         project_dir = self.path(project)
    #         content_dir = project_dir / 'content'
    #         content_dir.mkdir(exist_ok=True, parents=True)
            
    #         metadata_file = content_dir / Files.METADATA
    #         with open(metadata_file, 'w') as f:
    #             yaml.safe_dump(data, f)
            
    #         self.logger.info(f"Saved project data for {project.name}")
    #     except Exception as e:
    #         self.logger.error(f"Error saving project data: {e}")

    def rename(self, project: Project, old_name, new_name, **kwargs):
        """
        Rename local project directory.
        
        Args:
            project_ref: Reference to the project
            old_name: Old project name
            new_name: New project name
            **kwargs: Additional parameters
            
        Returns:
            dict: Result of the operation
        """
        try:                
            # Calculate paths
            old_dir = self.base_dir / old_name
            new_dir = self.base_dir / new_name
            
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
                
                # Setup the project filesystem
                self.setup(project)
        except Exception as e:
            self.logger.error(f"Error renaming local directory: {e}")