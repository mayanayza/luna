import os
import subprocess

from script.src.config import Config
from script.src.constants import Files, Status
from script.src.utils import (
    get_media_path,
    get_project_metadata,
    get_project_path,
    setup_logging,
)


class GithubHandler:

    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logging(__name__)
        if self.config.github_token:
            os.environ['GH_TOKEN'] = self.config.github_token
        else:
            self.logger.warning("No GitHub token found in environment")

    @property
    def url_path(self) -> str:
        return f"https://github.com/{self.config.github_username}"

    def create(self, name: str) -> None:
        """Initialize and set up git repository"""
        project_dir = get_project_path(self, name)

        try:
            os.chdir(project_dir)
            subprocess.run(['git', 'init'], check=True)
            subprocess.run(['git', 'add', Files.GITIGNORE, Files.METADATA], check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit with metadata, and .gitignore'], check=True)
            subprocess.run(['gh', 'repo', 'create', name, '--private', '--source=.'], check=True)
            subprocess.run(['git', 'branch', '-M', 'main'], check=True)
            subprocess.run(['git', 'push', '-u', 'origin', 'main'], check=True)
            self.logger.info(f"Successfully created GitHub repo for {name}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git initialization failed: {e}")
            raise

    def rename(self, old_name: str, new_name: str, new_path: str) -> None:
        """Rename GitHub repository and update remote URL"""
        try:
            os.chdir(new_path)
            
            # First get the current remote URL to verify the repository name
            subprocess.check_output(['git', 'remote', 'get-url', 'origin'], text=True).strip()
            
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

    def publish(self, name: str) -> None:

        project_dir = get_project_path(self, name)
        metadata = get_project_metadata(self, name)
        status = metadata['project']['status']
        description = metadata['project']['description']
        os.chdir(project_dir)
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)

        try:
            if result.stdout.strip():
                
                if status == Status.COMPLETE:
                    subprocess.run(['gh', 'repo', 'edit', '--homepage', f"{self.config.website_domain}/{name}"])

                if description:
                    subprocess.run(['gh', 'repo', 'edit', '--description', f"{description}"])

                subprocess.run(['git', 'add', '.'], check=True)
                subprocess.run(['git', 'commit', '-m', 'Publishing new files and updating readme'], check=True)
                subprocess.run(['git', 'push', 'origin', 'main'], check=True)
                self.logger.info(f"Git changes synced for project: {name}")
            else:
                self.logger.info(f"No git changes to publish for project: {name}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to publish github {name}: {e}")
            raise

    def stage_readme(self, name: str) -> None:
        """Generate README.md content from project metadata and content.md"""
        project_dir = get_project_path(self, name)
        metadata = get_project_metadata(self, name)
        project = metadata['project']
        
        with open(project_dir / Files.CONTENT, 'r') as f:
            content = f.read()

         # Build README content
        readme = f"# {project['display_name']}\n\n"
        readme += f"{content}\n## Media\n\n"
                
        # Add images section if images exist
        extensions = ("*.png","*.jpg","*.jpeg", "*.JPG", "*.JPEG")
        images = []
        for extension in extensions:
            images.extend( get_media_path(self, project_dir, 'images').glob(extension) )
        if images:
            readme += "\n### Images\n"
            for img in images:
                readme += f"![{img.stem}](media/images/{img.name})\n"
        
        # Add videos section if videos exist
        videos = list( get_media_path(self, project_dir, 'videos').glob('*.webm') )
        if videos:
            readme += "\n### Videos\n"
            for video in videos:
                readme += f"- [{video.stem}](media/videos/{video.name})\n"
        
        # Add models section if models exist
        models = list( get_media_path(self, project_dir, 'models').glob('*.glb'))
        if models:
            readme += "\n### 3D Models\n"
            for model in models:
                readme += f"- [{model.stem}](media/models/{model.name})\n"
        
        self.logger.info(f"Successfully staged README.md for {name}")

        with open(project_dir / Files.README, 'w') as f:
            f.write(readme)        