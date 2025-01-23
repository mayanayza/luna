import argparse
import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Load environment variables from .env file 🌫️ Paralysis
load_dotenv()

@dataclass
class ProjectConfig:
    base_dir: Path
    website_domain: str
    github_username: str
    github_token: str
    jekyll_dir: Path
    enable_things3: bool

    @property
    def github_url_path(self) -> str:
        return f"https://github.com/{self.github_username}"

    @property
    def templates_dir(self) -> Path:
        script_dir = Path(__file__).resolve().parent
        return script_dir.parent / 'templates'

    # Jekyll-specific paths
    @property
    def jekyll_posts_dir(self) -> Path:
        return self.jekyll_dir / '_posts'

    @property
    def jekyll_media_dir(self) -> Path:
        return self.jekyll_dir / 'media'

    @property
    def jekyll_pages_dir(self) -> Path:
        return self.jekyll_dir / '_pages'

class ProjectAutomation:

    def __init__(self, config: ProjectConfig):
        self.config = config
        self.setup_logging()
        self.setup_github()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    #     ____________    ______   _______________  __  ________________  ______  ______
    #    / ____/  _/ /   / ____/  / ___/_  __/ __ \/ / / / ____/_  __/ / / / __ \/ ____/
    #   / /_   / // /   / __/     \__ \ / / / /_/ / / / / /     / / / / / / /_/ / __/
    #  / __/ _/ // /___/ /___    ___/ // / / _, _/ /_/ / /___  / / / /_/ / _, _/ /___
    # /_/   /___/_____/_____/   /____//_/ /_/ |_|\____/\____/ /_/  \____/_/ |_/_____/

    # Directory structure constants
    BASE_DIRS = ['src', 'docs', 'hardware']
    MEDIA_TYPES = ['images', 'videos', 'models']
    
    # Template file names
    README_FILE = 'README.md'
    METADATA_FILE = 'metadata.yml'
    CONTENT_FILE = 'content.md'
    GITIGNORE_FILE = 'gitignore'

    def get_project_directories(self) -> list[tuple[Path, str]]:
        """Get list of all project directories and their formatted names"""
        try:
            projects = []
            for item in self.config.base_dir.iterdir():
                if item.is_dir() and (item / self.METADATA_FILE).exists():
                    projects.append((item, item.name))
            return projects
        except Exception as e:
            self.logger.error(f"Failed to read project directories: {e}")
            raise

    def get_project_path(self, name: str) -> Path:
        """Get the full path for a project"""
        return self.config.base_dir / name

    def get_media_path(self, project_dir: Path, media_type: str, internal: bool = False) -> Path:
        """Get the media path for a specific type"""
        base = 'media-internal' if internal else 'media'
        return project_dir / base / media_type

    def load_template(self, template_name: str) -> str:
        """Load a template file and return its contents"""
        template_path = self.config.templates_dir / template_name
        try:
            with open(template_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            self.logger.error(f"Template file not found: {template_path}")
            raise

    def create_file_structure(self, name: str, display_name: str) -> None:
        """Create the project directory structure and initialize files"""
        
        project_dir = self.get_project_path(name)

        for base_dir in self.BASE_DIRS:
            (project_dir / base_dir).mkdir(parents=True, exist_ok=True)

        # Create media directory structure
        for media_type in self.MEDIA_TYPES:
            self.get_media_path(project_dir, media_type).mkdir(parents=True, exist_ok=True)
            self.get_media_path(project_dir, media_type, internal=True).mkdir(parents=True, exist_ok=True)

        # Load and process templates
        date = datetime.now().strftime('%Y-%m-%d')
        template_vars = {
            'display_name': display_name,
            'name': name,
            'date': date
        }

        # Create content.md from template
        content_template = self.load_template(self.CONTENT_FILE)
        with open(project_dir / self.CONTENT_FILE, 'w') as f:
            f.write(content_template)

        # Create metadata.yml from template
        metadata_content = self.load_template(self.METADATA_FILE).format(**template_vars)
        with open(project_dir / self.METADATA_FILE, 'w') as f:
            f.write(metadata_content)

        # Create .gitignore from template
        gitignore_content = self.load_template(self.GITIGNORE_FILE)
        with open(project_dir / f".{self.GITIGNORE_FILE}", 'w') as f:
            f.write(gitignore_content)

    def rename_file_structure(self, old_name: str, old_display_name: str, old_path: str, new_name: str, new_display_name: str, new_path: str) -> None:
        # Update README.md
        readme_path = old_path / self.README_FILE
        if readme_path.exists():
            with open(readme_path, 'r') as f:
                readme_content = f.read()
            # Replace the project name in the header
            readme_content = readme_content.replace(f"# {old_display_name}", f"# {new_display_name}")
            with open(readme_path, 'w') as f:
                f.write(readme_content)

        # Update metadata
        with open(old_path / self.METADATA_FILE, 'r') as f:
            metadata = yaml.safe_load(f)
        metadata['project']['name'] = new_name
        metadata['project']['display_name'] = new_display_name
        
        # Save updated metadata
        with open(old_path / self.METADATA_FILE, 'w') as f:
            yaml.safe_dump(metadata, f, sort_keys=False, allow_unicode=True)
        
        # Rename local directory
        old_path.rename(new_path)

    #    ________________
    #   / ____/  _/_  __/
    #  / / __ / /  / /
    # / /_/ // /  / /
    # \____/___/ /_/

    def setup_github(self):
        """Configure GitHub credentials"""
        if self.config.github_token:
            os.environ['GH_TOKEN'] = self.config.github_token
        else:
            self.logger.warning("No GitHub token found in environment")

    def create_git_repo(self, name: str) -> None:
        """Initialize and set up git repository"""
        project_dir = self.get_project_path(name)

        try:
            os.chdir(project_dir)
            subprocess.run(['git', 'init'], check=True)
            subprocess.run(['git', 'add', f".{self.GITIGNORE_FILE}", self.METADATA_FILE], check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit with metadata, and .gitignore'], check=True)
            subprocess.run(['gh', 'repo', 'create', name, '--private', '--source=.'], check=True)
            subprocess.run(['git', 'branch', '-M', 'main'], check=True)
            subprocess.run(['git', 'push', '-u', 'origin', 'main'], check=True)
            self.logger.info(f"Successfully created GitHub repo for {name}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git initialization failed: {e}")
            raise

    def rename_git_repo(self, old_name: str, new_name: str, new_path: str) -> None:
        """Rename GitHub repository and update remote URL"""
        try:
            os.chdir(new_path)
            
            # First get the current remote URL to verify the repository name
            remote_url = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], 
                                              text=True).strip()
            
            # Commit local changes before renaming repository
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', f'Rename project to {new_name}'], check=True)
            
            # Rename the repository using the old name
            subprocess.run(['gh', 'repo', 'rename', new_name, '--repo', 
                          f'{self.config.github_username}/{old_name}'], check=True)
            
            # Update remote URL
            new_remote = f'git@github.com:{self.config.github_username}/{new_name}.git'
            subprocess.run(['git', 'remote', 'set-url', 'origin', new_remote], check=True)
            
            # Push changes
            subprocess.run(['git', 'push', 'origin', 'main'], check=True)
            
            self.logger.info(f"Successfully renamed GitHub repository to {new_name}")
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to update GitHub repository: {e}")

    def generate_readme(self, name: str) -> str:
        """Generate README.md content from project metadata and content.md"""
        project_dir = self.get_project_path(name)

        with open(project_dir / self.METADATA_FILE, 'r') as f:
            metadata = yaml.safe_load(f)

        project = metadata['project']
        status = metadata['project']['status']
        
        # Read content.md
        try:
            with open(project_dir / self.CONTENT_FILE, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            content = "Project content to be added..."

         # Build README content
        readme = f"# {project['display_name']}\n\n"

        if status == 'published':
            readme += f"[View on my website]({self.config.website_domain}/{name})\n\n"

        readme += f"{content}\n## Media\n\n"
                
        # Add images section if images exist
        extensions = ("*.png","*.jpg","*.jpeg", "*.JPG", "*.JPEG")
        images = []
        for extension in extensions:
            images.extend( self.get_media_path(project_dir, 'images').glob(extension) )
        if images:
            readme += "\n### Images\n"
            for img in images:
                readme += f"![{img.stem}](media/images/{img.name})\n"
        
        # Add videos section if videos exist
        videos = list( self.get_media_path(project_dir, 'videos').glob('*.webm') )
        if videos:
            readme += "\n### Videos\n"
            for video in videos:
                readme += f"- [{video.stem}](media/videos/{video.name})\n"
        
        # Add models section if models exist
        models = list( self.get_media_path(project_dir, 'models').glob('*.glb'))
        if models:
            readme += "\n### 3D Models\n"
            for model in models:
                readme += f"- [{model.stem}](media/models/{model.name})\n"
        
        self.logger.info(f"Successfully generated README.md for {name}")

        return readme

    #        __________ ____  ____    __
    #       / / ____/ //_/\ \/ / /   / /
    #  __  / / __/ / ,<    \  / /   / /
    # / /_/ / /___/ /| |   / / /___/ /___
    # \____/_____/_/ |_|  /_/_____/_____/

    def generate_jekyll_post(self, name: str) -> str:
        """Generate Jekyll post content from project metadata"""
        project_dir = self.get_project_path(name)

        with open(project_dir / self.METADATA_FILE, 'r') as f:
            metadata = yaml.safe_load(f)

        project = metadata['project']
        
        # Build front matter
        front_matter = {
            'layout': 'post',
            'title': strip_emoji(project['display_name']).strip(),
            'description': project.get('description', ''),
            'date': f"{project['date_created']} 15:01:35 +0300",
            'tags': project.get('tags', []),
            'github': f"{self.config.github_url_path}/{name}"
        }

        featured_image = project.get('featured_image')
        if featured_image:
            featured_image_path = f"/media/{project['name']}/images/{featured_image}"
            front_matter['image'] = featured_image_path
        
        # Generate content with media sections
        try:
            with open(project_dir / self.CONTENT_FILE, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            content = "Project content to be added..."
                
        # Add image gallery if images exist
        extensions = ("*.png","*.jpg","*.jpeg", "*.JPG", "*.JPEG")
        images = []
        for extension in extensions:
            images.extend( self.get_media_path(project_dir, 'images').glob(extension) )
        if images:
            content += '\n\n<div class="gallery-box">\n  <div class="gallery">\n'
            for img in images:
                if img.name != project.get('featured_image', ''):  # Skip featured image
                    content += f'    <img src="/media/{project["name"]}/images/{img.name}">\n'
            content += '  </div>\n</div>\n'
        
        # Add videos if they exist
        videos = list( self.get_media_path(project_dir, 'videos').glob('*.webm') )
        if videos:
            for video in videos:
                content += f'\n\n<video controls>\n  <source src="/media/{project["name"]}/videos/{video.name}" type="video/webm">\n</video>\n'
        
        # Add models if they exist
        models = list( self.get_media_path(project_dir, 'models').glob('*.glb'))
        if models:
            for model in models:
                content += f'\n\n<model-viewer src="/media/{project["name"]}/models/{model.name}" auto-rotate camera-controls></model-viewer>\n'
        
        self.logger.info(f"Successfully generated Jekyll post for {name}")

        # Combine front matter and content

        post = "---\n"
        post += f"{yaml.dump(front_matter, default_flow_style=False, sort_keys=False, allow_unicode=True)}\n"
        post += "---\n"
        post += f"[View on my GitHub]({self.config.github_url_path}/{name})\n"
        post += f"{content}\n"

        return post

    def generate_sync_roadmap(self) -> None:
        """Generate roadmap page from projects metadata"""
        projects = self.get_project_directories()
        in_progress = []
        backlog = []
        
        for project_dir, name in projects:
            with open(project_dir / self.METADATA_FILE, 'r') as f:
                metadata = yaml.safe_load(f)
                project = metadata['project']
                if project['status'] == 'in_progress':
                    in_progress.append(project)
                elif project['status'] == 'backlog':
                    backlog.append(project)
        
        # Sort by priority
        #in_progress.sort(key=lambda x: x.get('priority', 0), reverse=True)
        backlog.sort(key=lambda x: x.get('priority', 0), reverse=True)

        content = "---\n"
        content += "layout: page\n"
        content += "title: Roadmap\n"
        content += "permalink: /roadmap/\n"
        content += "---\n"
        
        content += "\n## In Progress\n"
        if in_progress:
            content += "\n| Project | Description |\n|---------|-------------|\n"
            for project in in_progress:
                content += f"| <a href='{self.config.github_url_path}/{project['name']}' target='_blank'>{project['display_name']}</a> | {project.get('description', '')} | \n"
        else:
            content += "Nothing currently in progress"
        
        content += "\n## Backlog\n"
        if backlog:
            content += "\n| Project | Description | Priority |\n|---------|-------------|----------|\n"
            for project in backlog:
                content += f"| <a href='{self.config.github_url_path}/{project['name']}' target='_blank'>{project['display_name']}</a> | {project.get('description', '')} | {project.get('priority', 0)} |\n"
        else:
            content += "Nothing currently in backlog"

        # Save roadmap
        self.config.jekyll_pages_dir.mkdir(exist_ok=True)
        with open(self.config.jekyll_pages_dir / 'roadmap.md', 'w') as f:
            f.write(content)

        self.logger.info("Successfully generated and synced roadmap")
    
    def sync_jekyll_media_files(self, source_dir: Path, dest_dir: Path) -> None:
        """Sync media files from project to Jekyll site"""
        if not source_dir.exists():
            return
            
        # Create destination directories
        for media_type in self.MEDIA_TYPES:
            (dest_dir / media_type).mkdir(parents=True, exist_ok=True)
            
            # Copy files
            source_type_dir = source_dir / media_type
            if source_type_dir.exists():
                for file in source_type_dir.iterdir():
                    if file.is_file():
                        shutil.copy2(file, dest_dir / media_type / file.name)

        self.logger.info("Successfully synced Jekyll media files")

    def rename_jekyll_files(self, old_name: str, new_name: str, display_name: str) -> None:
        """Update all Jekyll-related files when renaming a project"""
        try:
            # Rename post file in _posts directory
            jekyll_posts_dir = self.config.jekyll_posts_dir
            for post_file in jekyll_posts_dir.glob(f'*-{old_name}.md'):
                new_post_name = post_file.name.replace(old_name, new_name)
                new_post_path = jekyll_posts_dir / new_post_name
                
                # Update content before moving
                with open(post_file, 'r') as f:
                    content = f.read()
                
                # Update any paths in the content
                content = content.replace(f'/media/{old_name}/', f'/media/{new_name}/')
                
                # Write to new location
                with open(new_post_path, 'w') as f:
                    f.write(content)
                
                # Remove old file
                post_file.unlink()
                self.logger.info(f"Renamed Jekyll post to {new_post_name}")

            # Rename media directory
            old_media_dir = self.config.jekyll_media_dir / old_name
            if old_media_dir.exists():
                new_media_dir = self.config.jekyll_media_dir / new_name
                # Create parent directories if they don't exist
                new_media_dir.parent.mkdir(parents=True, exist_ok=True)
                old_media_dir.rename(new_media_dir)
                self.logger.info(f"Renamed media directory from {old_name} to {new_name}")

        except Exception as e:
            self.logger.error(f"Failed to rename Jekyll files: {e}")
            raise

    #   ________  _______   _____________
    #  /_  __/ / / /  _/ | / / ____/ ___/
    #   / / / /_/ // //  |/ / / __ \__ \
    #  / / / __  // // /|  / /_/ /___/ /
    # /_/ /_/ /_/___/_/ |_/\____//____/

    def create_things_project(self, display_name: str) -> None:
        """Create a project in Things 3 via AppleScript. Raises if creation fails."""
        if not self.config.enable_things3:
            return

        applescript = f'''
        tell application "Things3"
            set newProject to make new project with properties {{{{name:"{display_name}"}}}}
            set newProject's area to area "🎨 Art"
        end tell
        '''
        try:
            subprocess.run(['osascript', '-e', applescript], check=True)
            self.logger.info(f"Created Things 3 project: {display_name}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create Things 3 project: {e}")

    def rename_things_project(self, old_display_name: str, new_display_name: str) -> None:
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

    #    __________  __  _____  ______    _   ______  _____
    #   / ____/ __ \/  |/  /  |/  /   |  / | / / __ \/ ___/
    #  / /   / / / / /|_/ / /|_/ / /| | /  |/ / / / /\__ \
    # / /___/ /_/ / /  / / /  / / ___ |/ /|  / /_/ /___/ /
    # \____/\____/_/  /_/_/  /_/_/  |_/_/ |_/_____//____/

    def sync_project(self, name: str) -> None:
        """Generate readme and jekyll post, sync media to jekyll"""
        project_dir = self.get_project_path(name)
        jekyll_media_dir = self.config.jekyll_media_dir / name
        
        self.logger.info(f"Syncing project: {name}")

        try:
            # Read project metadata
            with open(project_dir / self.METADATA_FILE, 'r') as f:
                metadata = yaml.safe_load(f)
                
            # Generate and save readme content
            readme_content = self.generate_readme(name)
            with open(project_dir / self.README_FILE, 'w') as f:
                f.write(readme_content)

            # Check if there are git changes
            os.chdir(project_dir)
            result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
            
            if result.stdout.strip():
                # Only commit and push if there are changes
                subprocess.run(['git', 'add', '.'], check=True)
                subprocess.run(['git', 'commit', '-m', 'Syncing new files and updating readme'], check=True)
                subprocess.run(['git', 'push', 'origin', 'main'], check=True)
                self.logger.info(f"Git changes synced for project: {name}")
            else:
                self.logger.info(f"No git changes to sync for project: {name}")

            # Generate and sync Jekyll post content
            if metadata['project']['status'] == 'published':
                post_content = self.generate_jekyll_post(name)
                post_date = metadata['project']['date_created']
                post_file = self.config.jekyll_posts_dir / f"{post_date}-{name}.md"
                with open(post_file, 'w') as f:
                    f.write(post_content)
                    
                # Sync media files
                self.sync_jekyll_media_files(project_dir / 'media', jekyll_media_dir)
                        
            self.logger.info(f"Successfully synced project: {name}")
        except Exception as e:
            self.logger.error(f"Failed to sync project: {e}")
            raise

    def create_project(self, name: str, display_name: str) -> None:

        self.create_file_structure(name, display_name)
        self.create_git_repo(name)
        self.sync_project(name)
        self.create_things_project(display_name)
    
    def list_projects(self) -> None:
        """List all projects with their details"""
        projects = self.get_project_directories()
        
        if not projects:
            self.logger.info("No projects found")
            return
            
        self.logger.info(f"\n -- Found {len(projects)} projects: --")
        for project_dir, name in sorted(projects):
            try:
                with open(project_dir / self.METADATA_FILE, 'r') as f:
                    metadata = yaml.safe_load(f)
                display_name = metadata['project']['display_name']
                date = metadata['project']['date_created']
                status = metadata['project']['status']
                self.logger.info(f"{display_name} ({name}); Created: {date}; Status: {status}")
            except Exception as e:
                self.logger.error(f"Error reading project {name}: {e}")

    def sync_all_projects(self) -> None:
        """Sync all projects that need updating"""
        projects = self.get_project_directories()
        for project_dir, name in projects:
            self.sync_project(name)
            self.logger.info("")
        self.generate_sync_roadmap()

    def rename_project(self, old_name: str, new_name: str, new_display_name: str) -> None:
        """Rename a project locally and on GitHub"""        
        old_path = self.config.base_dir / old_name
        new_path = self.config.base_dir / new_name
        
        if not old_path.exists():
            raise ValueError(f"Project {old_name} not found")
        if new_path.exists():
            raise ValueError(f"Project {new_name} already exists")
            
        try:

            with open(old_path / self.METADATA_FILE, 'r') as f:
                metadata = yaml.safe_load(f)
                old_display_name = metadata['project']['display_name']

            self.rename_things_project(old_display_name, new_display_name)
            self.rename_file_structure(old_name, old_display_name, old_path, new_name, new_display_name, new_path)
            self.rename_jekyll_files(old_name, new_name, new_display_name)
            self.rename_git_repo(old_name, new_name, new_path)

            self.logger.info(f"Successfully renamed project from {old_name} to {new_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to rename project: {e}")

def strip_emoji(text: str) -> str:
    """Remove emoji characters from text"""
    emoji_pattern = re.compile("[\U0001F000-\U0001F6FF]|[\U0001F900-\U0001F9FF]|[\u2600-\u26FF]|[\u2700-\u27BF]|[\uFE00-\uFE0F]")
    return emoji_pattern.sub('', text).strip()

def get_formatted_name(name: str) -> str:
    # Remove emoji and other special characters, convert to lowercase
    cleaned = strip_emoji(name)
    cleaned = re.sub(r'[^a-zA-Z0-9\s-]', '', cleaned)
    
    # Convert to kebab-case
    formatted = cleaned.strip().lower().replace(' ', '-')
    formatted = re.sub(r'-+', '-', formatted)
    
    return formatted

def prompt_for_name() -> tuple[str, str]:
    """Prompt user for project name and return (name, formatted_name)"""
    display_name = input("Enter project display name (e.g. '🌱 Plant Autowater; a canonical name will be generated like plant-autowater.'): ").strip()
    if not display_name:
        raise ValueError("Project name cannot be empty")
    
    name = get_formatted_name(display_name)
    
    print("\nProject details:")
    print(f"Name: {name}")
    print(f"Formatted name: {display_name}")
    
    confirm = input("\nConfirm these details? (y/n): ").strip().lower()
    if confirm != 'y':
        raise ValueError("Project creation cancelled by user")
    
    return name, display_name

def prompt_for_new_name(old_name: str) -> tuple[str, str]:
    """Prompt user for new project name and return (name, formatted_name)"""
    new_display_name = input("Enter project display name (e.g. '🌱 Plant Autowater; a canonical name will be generated like plant-autowater.'): ").strip()
    if not new_display_name:
        raise ValueError("New project name cannot be empty")
    
    new_name = get_formatted_name(new_display_name)
    
    print("\nRename details:")
    print(f"Old name: {old_name}")
    print(f"New name: {new_name}")
    print(f"New display name: {new_display_name}")
    
    confirm = input("\nConfirm these details? (y/n): ").strip().lower()
    if confirm != 'y':
        raise ValueError("Project rename cancelled by user")
    
    return new_name, new_display_name

def main():
    parser = argparse.ArgumentParser(description='Project Automation Tool')
    parser.add_argument('--command', choices=['create', 'sync', 'rename', 'list'], default='create', 
                       help='Command to execute')
    parser.add_argument('--name', help='Project name for renaming or syncing')
    parser.add_argument('--all', action='store_true', help='Flag to sync all projects instead of a specific named project')
    args = parser.parse_args()

    # Calculate templates directory relative to script location

    config = ProjectConfig(
        base_dir=Path(os.environ.get('PROJECT_BASE_DIR')),
        website_domain=os.environ.get('WEBSITE_DOMAIN'),
        github_username=os.environ.get('GITHUB_USERNAME'),
        github_token=os.environ.get('GITHUB_TOKEN'),
        jekyll_dir=Path(os.environ.get('JEKYLL_DIR')),
        enable_things3=os.environ.get('ENABLE_THINGS3', 'true').lower() == 'true'
    )

    try:
        automation = ProjectAutomation(config)
        
        if args.command == 'create':
            name, display_name = prompt_for_name()
            automation.create_project(name, display_name)
            automation.generate_sync_roadmap()
            
        elif args.command == 'list':
            automation.list_projects()

        elif args.command == 'sync':
            if args.name:
                automation.sync_project(args.name)
                automation.generate_sync_roadmap()
            elif args.all:
                automation.sync_all_projects()
            else:
                parser.error("Either --name or --all must be specified for sync command")
                
        elif args.command == 'rename':
            if not args.name:
                parser.error("--name is required for rename command")
            new_name, new_display_name = prompt_for_new_name(args.name)
            automation.rename_project(args.name, new_name, new_display_name)
            
    except Exception as e:
        logging.error(f"Operation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()