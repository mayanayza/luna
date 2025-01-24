
from script.src.config import Config
from script.src.output.github import GithubHandler
from script.src.output.jekyll import JekyllHandler
from script.src.output.pdf import PDFHandler
from script.src.output.things import ThingsHandler
from script.src.setup import SetupHandler
from script.src.utils import (
    get_project_metadata,
    setup_logging,
)


class Automation:

    def __init__(self, config: Config):
        self.config = config
        self.github = GithubHandler(config)
        self.jekyll = JekyllHandler(config)
        self.things = ThingsHandler(config)
        self.setup = SetupHandler(config)
        self.pdf = PDFHandler(config)
        self.logger = setup_logging(__name__)

    def publish_website(self, projects: list) -> None:
        for name in projects:
            self.github.stage_readme(name)
            self.github.publish(name)

    def publish_github(self, projects: list) -> None:
        for name in projects:
            self.jekyll.stage_post(name)                    
            self.jekyll.stage_media(name)
        self.jekyll.stage_roadmap()
        self.jekyll.publish()

    def publish_pdf(self, projects: list, collate_images: bool=False, filename_prepend: str=''):
        for name in projects:
            self.pdf.stage_media(name, filename_prepend)
            self.pdf.stage_pdf(name, collate_images)
        self.pdf.publish()                    

    def create_project(self, name: str, display_name: str) -> None:
        self.setup.create(name, display_name)
        self.github.create(name)
        self.things.create(display_name)
        self.publish_project(name)
    
    def list_projects(self, projects) -> None:
        """List projects with their details"""        
        if not projects:
            self.logger.info("No projects found")
            return
            
        self.logger.info(f"\n -- Found {len(projects)} projects: --")
        for name in sorted(projects):
            try:
                metadata = get_project_metadata(self, name)
                display_name = metadata['project']['display_name']
                date = metadata['project']['date_created']
                status = metadata['project']['status']
                self.logger.info(f"{display_name} ({name}); Created: {date}; Status: {status}")
            except Exception as e:
                self.logger.error(f"Error reading project {name}: {e}")

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

            self.setup.rename(old_name, old_display_name, old_path, new_name, new_display_name, new_path)
            
            self.things.rename(old_display_name, new_display_name)
            self.jekyll.rename(old_name, new_name, new_display_name)
            self.github.rename(old_name, new_name, new_path)
            self.publish_project(new_name)

            self.logger.info(f"Successfully renamed project from {old_name} to {new_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to rename project: {e}")