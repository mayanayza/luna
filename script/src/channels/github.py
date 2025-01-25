import os
import subprocess

from script.src.channels._channel import Channel
from script.src.config import Config
from script.src.constants import MEDIA, Files, Status
from script.src.utils import get_media_files, get_project_metadata, get_project_path


class GithubHandler(Channel):

    def __init__(self, config: Config):

        init = {
            'name': __name__,
            'class_name':self.__class__.__name__,
            'config': config
        }
            
        super().__init__(**init)

        self.media = {
           'images': MEDIA['images'],
           # 'videos': ("*.mp4", "*.webm"),
           # 'models': ("*.glb", "*.mp4"),
           # 'audio': ("*.mp3", "*.wav"),
           # 'docs': ("*.pdf",)
        }

    def create(self, name: str) -> None:
        
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
            self.logger.error(f"GitHub initialization failed: {e}")
            raise

    def publish(self, name: str, commit_message: str) -> None:

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
                subprocess.run(['git', 'commit', '-m', f"{commit_message}"], check=True)
                subprocess.run(['git', 'push', 'origin', 'main'], check=True)
                self.logger.info(f"Git changes synced for project: {name}")
            else:
                self.logger.info(f"No changes to publish for project: {name}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to publish GitHub {name}: {e}")
            raise

    def stage(self, name: str) -> None:
        project_dir = get_project_path(self, name)
        readme = self.generate_readme(name)
        with open(project_dir / Files.README, 'w') as f:
            f.write(readme)  

    def generate_readme(self, name):

        try:
        
            template_path = "md/readme.md"

            context = {}
            for media_type in self.media:
                context[media_type] = get_media_files(self, name, media_type, self.media[media_type])

            readme = self.tp.process_template(name, template_path, context)
            self.logger.info(f"Generated GitHub readme for {name}")
            return readme

        except Exception as e:
            self.logger.error(f"Failed to generate GitHub readme for {name}: {e}")
            raise

    def rename(self, old_name: str, new_name: str) -> None:
        
        try:
            project_dir = get_project_path(self, new_name)
            os.chdir(project_dir)
            
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
            
            self.logger.info(f"Successfully renamed GitHub repo to {new_name}")
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to update GitHub repo: {e}")

    def delete(self, name: str) -> None:
        try:
            subprocess.run(['gh', 'repo', 'delete', name], check=True)
            self.logger.info(f"Deleted GitHub repo for {name}")
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to update GitHub repo for {name}: {e}")
