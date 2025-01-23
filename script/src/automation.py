
from script.src.config import Config
from script.src.constants import Status
from script.src.file import FileHandler
from script.src.github import GithubHandler
from script.src.jekyll import JekyllHandler
from script.src.things import ThingsHandler
from script.src.utils import (
    get_project_directories,
    get_project_metadata,
    setup_logging,
)


class Automation:

    def __init__(self, config: Config):
        self.config = config
        self.github = GithubHandler(config)
        self.jekyll = JekyllHandler(config)
        self.things = ThingsHandler(config)
        self.files = FileHandler(config)
        self.logger = setup_logging(__name__)

    def publish_project(self, name: str) -> None:
        """Generate and publish to various platforms"""
        
        metadata = get_project_metadata(self, name)
        
        
        try:                
            self.github.stage_readme(name)
            self.github.publish(name)

            if metadata['project']['status'] == Status.COMPLETE:

                self.github.publish_repo_post_info(name)
                self.jekyll.stage_post(name)                    
                self.jekyll.stage_media(name)
                self.jekyll.publish()
                        
                self.logger.info(f"Successfully published project: {name}")
        except Exception as e:
            self.logger.error(f"Failed to sync project: {e}")
            raise

    def publish_roadmap(self) -> None:
        self.jekyll.stage_roadmap()
        self.jekyll.publish()

    def create_project(self, name: str, display_name: str) -> None:
        self.files.create(name, display_name)
        self.github.create(name)
        self.things.create(display_name)
        self.publish_project(name)
    
    def list_projects(self) -> None:
        """List all projects with their details"""
        projects = get_project_directories(self)
        
        if not projects:
            self.logger.info("No projects found")
            return
            
        self.logger.info(f"\n -- Found {len(projects)} projects: --")
        for project_dir, name in sorted(projects):
            try:
                metadata = get_project_metadata(self, name)
                display_name = metadata['project']['display_name']
                date = metadata['project']['date_created']
                status = metadata['project']['status']
                self.logger.info(f"{display_name} ({name}); Created: {date}; Status: {status}")
            except Exception as e:
                self.logger.error(f"Error reading project {name}: {e}")

    def publish_all_projects(self) -> None:
        """Publish all projects that need updating"""
        projects = get_project_directories(self)
        for project_dir, name in projects:
            self.publish_project(name)
            self.logger.info("-----")

    def rename_project(self, old_name: str, new_name: str, new_display_name: str) -> None:
        """Rename a project locally and on GitHub"""        
        old_path = self.config.base_dir / old_name
        new_path = self.config.base_dir / new_name
        
        if not old_path.exists():
            raise ValueError(f"Project {old_name} not found")
        if new_path.exists():
            raise ValueError(f"Project {new_name} already exists")
            
        try:
            
            metadata = get_project_metadata(self, old_name)
            old_display_name = metadata['project']['display_name']

            self.things.rename(old_display_name, new_display_name)
            self.files.rename(old_name, old_display_name, old_path, new_name, new_display_name, new_path)
            self.jekyll.rename(old_name, new_name, new_display_name)
            self.github.rename(old_name, new_name, new_path)
            self.publish_project(new_name)

            self.logger.info(f"Successfully renamed project from {old_name} to {new_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to rename project: {e}")