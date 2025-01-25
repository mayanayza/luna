
import re

from script.src.channels.github import GithubHandler
from script.src.channels.pdf import PDFHandler
from script.src.channels.website import WebsiteHandler
from script.src.config import Config
from script.src.constants import Files
from script.src.setup.files import FileHandler
from script.src.setup.things import ThingsHandler
from script.src.utils import (
    get_project_metadata,
    get_project_path,
    setup_logging,
    strip_emoji,
)


class Automation:

    def __init__(self, config: Config):
        self.config = config
        self.github = GithubHandler(config)
        self.website = WebsiteHandler(config)
        self.things = ThingsHandler(config)
        self.setup = FileHandler(config)
        self.pdf = PDFHandler(config)
        self.logger = setup_logging(__name__)

    def publish_github(self, projects: list, commit_message: str) -> None:
        for name in projects:
            self.github.stage(name)
            self.github.publish(name, commit_message)

    def publish_web(self, projects: list) -> None:
        staged_projects = []
        for name in projects:
            staged_projects.append( self.website.stage(name) )

        staged_projects = [p for p in staged_projects if p.strip()]
        
        self.website.publish( "Updating content for " + ", ".join(staged_projects) )

    def publish_pdf(self, projects: list, collate_images: bool, filename_prepend: str) -> None:
        for name in projects:
            self.pdf.stage(name, collate_images, filename_prepend)
        self.pdf.publish()                    

    def create_project(self, name: str, display_name: str) -> None:

        name, display_name, title = self.prompt_for_name()

        self.setup.create(name, display_name, title)
        self.github.create(name)
        self.things.create(display_name)
    
    def list_projects(self) -> None:
        """List projects with their details"""
        projects = []
        for item in self.config.base_dir.iterdir():
            if item.is_dir() and (item / Files.METADATA).exists():
                projects.append(item.name)                
        self.logger.info(f"\n -- Listing {len(projects)} projects: --")
        for name in sorted(projects):
            try:
                metadata = get_project_metadata(self, name)
                display_name = metadata['project']['display_name']
                date = metadata['project']['date_created']
                status = metadata['project']['status']
                self.logger.info(f"{display_name} ({name}); Created: {date}; Status: {status}")
            except Exception as e:
                self.logger.error(f"Error reading project {name}: {e}")

    def rename_project(self) -> None:
        """Rename a project locally and on GitHub"""                    
        try:
            
            old_name, new_name, new_display_name, new_title = self.prompt_for_new_name()

            metadata = get_project_metadata(self, old_name)
            old_display_name = metadata['project']['display_name']

            self.setup.rename(old_name, new_name, new_title, new_display_name)
            self.things.rename(old_display_name, new_display_name)

            self.website.rename(old_name, new_name, new_display_name)
            self.website.stage(new_name)
            self.github.rename(old_name, new_name)
            self.github.stage(new_name)

            self.logger.info(f"Successfully renamed project from {old_name} to {new_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to rename project: {e}")

    def get_formatted_name(self, display_name: str) -> str:
        # Remove emoji and other special characters, convert to lowercase
        title = strip_emoji(display_name)
        title = re.sub(r'[^a-zA-Z0-9\s-]', '', title)
        
        # Convert to kebab-case
        name = title.strip().lower().replace(' ', '-')
        name = re.sub(r'-+', '-', name)
        
        return title, name

    def prompt_for_name(self) -> tuple[str, str]:
        """Prompt user for project name and return (name, formatted_name)"""
        display_name = input("Enter project display name (e.g. '🌱 Project Name; a canonical name will be generated like project-name.'): ").strip()
        if not display_name:
            raise ValueError("Project name cannot be empty")
        
        title, name = self.get_formatted_name(display_name)
        
        print("\nProject details:")
        print(f"Name: {name}")
        print(f"Title: {title}")
        print(f"Display name: {display_name}")
        
        confirm = input("\nConfirm these details? (y/n): ").strip().lower()
        if confirm != 'y':
            raise ValueError("Project creation cancelled by user")
        
        return name, display_name, title

    def prompt_for_new_name(self) -> tuple[str, str]:
        """Prompt user for new project name and return (name, formatted_name)"""
        old_name = input("Enter name of project you would like to rename")
        new_display_name = input("Enter project display name (e.g. '🌱 Project Name; a canonical name will be generated like project-name.'): ").strip()
        if not new_display_name:
            raise ValueError("New project name cannot be empty")

        new_name, new_display_name, new_title = self.get_formatted_name(new_display_name)

        old_project_dir = get_project_path(self, old_name)
        new_project_dir = get_project_path(self, new_name)

        if not old_project_dir.exists():
            raise ValueError(f"Project {old_name} not found")
        if new_project_dir.exists():
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