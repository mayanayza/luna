import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import yaml

from src.script.channels._channel import Channel
from src.script.config import Config
from src.script.constants import Files, Media
from src.script.utils import (
    format_name,
    get_project_metadata,
    get_project_path,
    is_project,
)


class ProjectHandler(Channel):
    def __init__(self, config: Config, github_handler=None, things_handler=None, files_handler=None, website_handler=None, raw_handler=None):
        init = {
            'name': __name__,
            'class_name': self.__class__.__name__,
            'config': config
        }
            
        super().__init__(**init)
        
        # Dependencies for project operations
        self.github = github_handler
        self.website = website_handler
        self.raw = raw_handler
        
    def get_commands(self):
        """Return commands supported by Project handler"""
        return {
            'create': self.handle_create,
            'list': self.handle_list,
            'rename': self.handle_rename,
            'delete': self.handle_delete,
        }
        
    def handle_create(self, **kwargs):
        """Handle project creation command"""
        self.create_project()
    
    def handle_list(self, **kwargs):
        """Handle project listing command"""
        sort_by = kwargs.get('sort_by', 'name')
        filter_status = kwargs.get('status', None)
        self.list_projects(sort_by, filter_status)
    
    def handle_rename(self, **kwargs):
        """Handle project renaming command"""
        self.rename_project()
    
    def handle_delete(self, **kwargs):
        """Handle project deletion command"""
        projects = kwargs.get('projects', [])
        if projects:
            self.delete_project(projects[0])
        else:
            self.delete_project()
    
    def create_project(self) -> None:
        """Create a new project with user input"""
        name, display_name, title = self.prompt_for_display_name()
        create_github = self.prompt_create_github()

        self.create_files(name, display_name, title)
        self.create_things3(display_name)
        if create_github and self.github:
            self.github.create(name)
            
        self.logger.info(f"Successfully created project: {display_name}")
    
    def create_files(self, name: str, display_name: str, title: str) -> None:
        """Create the project directory structure and initialize files"""
        try:
            project_dir = get_project_path(self, name)
            templates_dir = Path(os.getcwd()) / 'src' / 'script' / 'templates' / 'setup'
            project_dir.mkdir()

            (project_dir / 'src').mkdir(parents=True, exist_ok=True)
            (project_dir / 'content').mkdir(parents=True, exist_ok=True)
            (project_dir / 'media').mkdir(parents=True, exist_ok=True)
            (project_dir / 'media-internal').mkdir(parents=True, exist_ok=True)
            # Create media directory structure

            for media in Media.ALL_TYPES:
                (project_dir / 'media' / media.TYPE).mkdir(parents=True, exist_ok=True)
                (project_dir / 'media-internal' / media.TYPE).mkdir(parents=True, exist_ok=True)

            # Load and process templates
            date = datetime.now().strftime('%Y-%m-%d')
            template_vars = {
                'display_name': display_name,
                'name': name,
                'title': title,
                'date': date
            }

            # Create metadata.yml from template
            metadata = open(templates_dir / Files.METADATA).read().format(**template_vars)
            with open(project_dir / 'content' / Files.METADATA, 'w') as f:
                f.write(metadata)

            open(project_dir / 'content/content.md', 'w').close()
            open(project_dir / 'content/README.md', 'w').close()

            shutil.copy(templates_dir / Files.GITIGNORE, project_dir / Files.GITIGNORE)

            self.logger.info(f"Created project files for {name}")
        except Exception as e:
            self.logger.error(f"Failed to create project files for {name}: {e}")

    def create_things3(self, display_name: str) -> None:
        """Create a project in Things 3 via AppleScript. Raises if creation fails."""
        if not self.config.enable_things3:
            return

        applescript = f'''
        tell application "Things3"
            set newProject to make new project with properties {{{{name:"{display_name}"}}}}
            set newProject's area to area "{self.config.things3_area}"
        end tell
        '''
        try:
            subprocess.run(['osascript', '-e', applescript], check=True)
            self.logger.info(f"Created Things 3 project: {display_name}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create Things 3 project: {e}")


    def list_projects(self, sort_by='name', filter_status=None) -> None:
        """List projects with their details, with sorting and filtering options"""
        projects = []
        for item in self.config.base_dir.iterdir():
            if is_project(self, item):
                try:
                    metadata = get_project_metadata(self, name=item.name)
                    
                    # Only add projects matching the status filter if specified
                    if filter_status and metadata['project']['status'] != filter_status:
                        continue
                        
                    projects.append({
                        'name': item.name,
                        'display_name': metadata['project']['display_name'],
                        'date': metadata['project']['date_created'],
                        'status': metadata['project']['status'],
                        'priority': metadata['project']['priority']
                    })
                except Exception as e:
                    self.logger.error(f"Error reading project {item.name}: {e}")
        
        # Sort projects based on specified field
        if sort_by == 'name':
            sorted_projects = sorted(projects, key=lambda x: x['name'])
        elif sort_by == 'date':
            sorted_projects = sorted(projects, key=lambda x: x['date'], reverse=True)
        elif sort_by == 'priority':
            sorted_projects = sorted(projects, key=lambda x: x['priority'], reverse=True)
        elif sort_by == 'status':
            sorted_projects = sorted(projects, key=lambda x: x['status'])
        else:
            sorted_projects = projects
        
        # Display projects
        self.logger.info(f"\n -- Listing {len(sorted_projects)} projects: --")
        for project in sorted_projects:
            self.logger.info(
                f"{project['display_name']} ({project['name']}); " +
                f"Created: {project['date']}; Status: {project['status']}; " +
                f"Priority: {project['priority']}"
            )
    
    def rename_project(self) -> None:
        """Rename a project locally and on GitHub"""                    
        try:
            old_name, new_name, new_display_name, new_title = self.prompt_for_new_display_name()

            metadata = get_project_metadata(self, old_name)
            old_display_name = metadata['project']['display_name']

            self.rename_files(old_name, new_name, new_display_name, new_title)
            self.rename_things3(old_display_name, new_display_name)

            if self.website:
                self.website.rename(old_name, new_name)
                self.website.stage(new_name)
            if self.github:
                self.github.rename(old_name, new_name)
                self.github.stage(new_name)

            self.logger.info(f"Successfully renamed project from {old_name} to {new_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to rename project: {e}")
    
    def rename_files(self, old_name: str, new_name: str, new_display_name: str, new_title: str) -> None:
        # Update metadata
        try:
            metadata = get_project_metadata(self, old_name)
            metadata['project']['name'] = new_name
            metadata['project']['display_name'] = new_display_name
            metadata['project']['title'] = new_title

            old_project_dir = get_project_path(self, old_name)
            new_project_dir = get_project_path(self, new_name)
            
            # Save updated metadata
            with open(old_project_dir / "content" / Files.METADATA, 'w') as f:
                yaml.safe_dump(metadata, f, sort_keys=False, allow_unicode=True)
            
            # Rename local directory
            old_project_dir.rename(new_project_dir)
            self.logger.info(f"Renamed project files from {old_name} to {new_name}")
        except Exception as e:
            self.logger.error(f"Failed to rename project files for {old_name}: {e}")

    def rename_things3(self, old_display_name: str, new_display_name: str) -> None:
        """Rename a project in Things 3"""
        if not self.config.enable_things3:
            return

        applescript = f'''
        tell application "Things3"
            set oldProject to first project whose name = "{old_display_name}"
            set oldProject's name to "{new_display_name}"
        end tell
        '''
        try:
            subprocess.run(['osascript', '-e', applescript], check=True)
            self.logger.info(f"Renamed Things 3 project from '{old_display_name}' to '{new_display_name}'")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to rename Things 3 project: {e}")


    def delete_project(self, name=None) -> None:
        """Delete a project by name, or prompt for a name if not provided"""
        try:
            if not name:
                name = self.prompt_for_name()
            
            # Confirm deletion
            confirm = input(f"Are you sure you want to delete project '{name}'? This cannot be undone. (y/N): ").strip().lower()
            if confirm != 'y':
                self.logger.info("Deletion cancelled.")
                return
                
            self.delete_files(name)
            self.delete_things3(name)
            
            if self.github:
                self.github.delete(name)
            if self.website:
                self.website.delete(name)
            if self.raw:
                self.raw.delete(name)
                
            self.logger.info(f"Successfully deleted project {name}")
        except Exception as e:
            self.logger.error(f"Failed to delete project: {e}")
    
    def delete_files(self, name: str) -> None:
        try:
            
            project_dir = get_project_path(self, name)
            shutil.rmtree(project_dir)
            self.logger.info(f"Deleted project files for {name}")
        except Exception as e:
            self.logger.error(f"Failed to delete project files for {name}: {e}")

    def delete_things3(self, name: str) -> None:
        print('TODO: Implement things delete functionality')


    def prompt_for_name(self) -> str:
        name = input("Enter project name:").strip()
        project_dir = get_project_path(self, name)
        if not Path(project_dir).exists():
            raise ValueError(f"Project {name} not found")
        else:
            return name

    def prompt_create_github(self):
        create_github = input("Create github repo for this project (y/N)?")
        if create_github == 'y':
            return True
        elif create_github == 'N':
            return False
        else:
            self.logger.info("Invalid input.")
            return self.prompt_create_github()

    def prompt_for_display_name(self) -> tuple:
        """Prompt user for project name and return (name, formatted_name)"""
        display_name = input("Enter project display name (e.g. '🌱 Project Name; a canonical name will be generated like project-name.'): ").strip()
        if not display_name:
            raise ValueError("Project name cannot be empty")
        
        name, title = format_name(self, display_name)
        
        print("\nProject details:")
        print(f"Name: {name}")
        print(f"Title: {title}")
        print(f"Display name: {display_name}")
        
        confirm = input("\nConfirm these details? (y/n): ").strip().lower()
        if confirm != 'y':
            raise ValueError("Project creation cancelled by user")
        
        return name, display_name, title

    def prompt_for_new_display_name(self) -> tuple:
        """Prompt user for new project name and return (old_name, new_name, new_display_name, new_title)"""
        old_name = input("Enter name of project you would like to rename: ")
        new_display_name = input("Enter project display name (e.g. '🌱 Project Name; a canonical name will be generated like project-name.'): ").strip()
        if not new_display_name:
            raise ValueError("New project name cannot be empty")

        new_name, new_title = format_name(self, new_display_name)

        old_project_dir = get_project_path(self, old_name)
        new_project_dir = get_project_path(self, new_name)

        if not Path(old_project_dir).exists():
            raise ValueError(f"Project {old_name} not found")
        if Path(new_project_dir).exists():
            raise ValueError(f"Project {new_name} already exists")
        
        print("\nRename details:")
        print(f"Old name: {old_name}")
        print(f"New name: {new_name}")
        print(f"New title: {new_title}")
        print(f"New display name: {new_display_name}")
        
        confirm = input("\nConfirm these details? (y/n): ").strip().lower()
        if confirm != 'y':
            raise ValueError("Project rename cancelled by user")
        
        return old_name, new_name, new_display_name, new_title