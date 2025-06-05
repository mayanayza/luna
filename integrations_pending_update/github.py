
import os
import subprocess
from typing import Dict

from src.script.constants import Files, Media, Status
from src.script.integration._integration import Integration
from src.script.integration._registry import IntegrationRegistry
from src.script.project._project import Project


class GithubIntegration(Integration):

    def __init__(self, registry: IntegrationRegistry):

        config = {
            'name': 'github',
            'env': {
                'github_token':'GITHUB_TOKEN',
                'github_username':'GITHUB_USERNAME',   
            },
            'project_fields':{
                'show_written_content': False,
            },
            'handlers':{
                'stage':[{
                    'function': self.stage,
                    'scope': 'project'
                }],
                'publish':[{
                    'function': self.publish,
                    'scope': 'project'
                }]
            },
            'apis':{
                'cli': self.cli
            }
        }
            
        super().__init__(config, registry)

    @property
    def base_url(self):
        f"https://github.com/{self.env['github_username']}"
        
    @property
    def project_url(self, project: Project):
        return self.base_url / project.name

    @property
    def is_public(self, project: Project) -> bool:
        os.chdir(self.path)
        visibility = subprocess.run(['gh', 'repo', 'view', '--json', 'visibility', '-q', '.visibility'], capture_output=True, text=True)
        visibility = visibility.stdout.strip().upper()
        if visibility == 'PUBLIC':
            return True
        else:
            return False

    def cli(self):
        """Register CLI arguments needed by this integration."""
        # Use _add_argument which safely handles duplicates
        cli = self.registry.apis.get('cli')
        cli._add_argument('--commit-message', '-cm', default='', help='Commit message for any integration which commits to github')
                
    def setup(self, project: Project, **kwargs) -> None:
        create_github = input("Create github repo for this project (y/N)?")
        if create_github == 'y':
            os.chdir(project.local.path)
            subprocess.run(['git', 'init'], check=True)
            subprocess.run(['git', 'add', Files.GITIGNORE], check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit with metadata, and .gitignore'], check=True)
            subprocess.run(['gh', 'repo', 'create', project.name, '--private', '--source=.'], check=True)
            subprocess.run(['git', 'branch', '-M', 'main'], check=True)
            subprocess.run(['git', 'push', '-u', 'origin', 'main'], check=True)

    def rename(self, project: Project, new: Dict) -> None:
        os.chdir(project.local.path)
        
        # First get the current remote URL to verify the repository name
        subprocess.check_output(['git', 'remote', 'get-url', 'origin'], text=True).strip()
        
        # Commit local changes before renaming repository
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', f'Rename project to {new.name}'], check=True)
        
        # Rename the repository using the old name
        subprocess.run(['gh', 'repo', 'rename', new.name, '--repo', 
                      f'{self.env['github_username']}/{project.name}'], check=True)
        
        # Update remote URL
        new_remote = f'git@github.com:{self.env['github_username']}/{new.name}.git'
        subprocess.run(['git', 'remote', 'set-url', 'origin', new_remote], check=True)
        
        # Push changes
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)

    def remove(self, project: Project, **kwargs) -> None:
        subprocess.run(['gh', 'repo', 'delete', project.name], check=True)

    def stage(self, project: Project, **kwargs) -> None:
        readme = self._generate_readme(project)
        with open(project.local.path / Files.README, 'w') as f:
            f.write(readme)  

    def publish(self, project: Project, **kwargs) -> None:

        commit_message = kwargs.get('commit_message', 'Update project content')

        status = project.metadata['status']
        tagline = project.metadata['tagline']
        os.chdir(project.local.path)
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)

        if result.stdout.strip():
            
            if status == Status.COMPLETE and project.has_integration('website') > 0:
                # TODO: only use this if project has the website integration AND route calls through website namespace
                subprocess.run(['gh', 'repo', 'edit', '--homepage', f"{project.website.project_url}"])

            if tagline:
                subprocess.run(['gh', 'repo', 'edit', '--description', f"{tagline}"])

            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', f"{commit_message}"], check=True)
            subprocess.run(['git', 'push', 'origin', 'main'], check=True)
            self.logger.info(f"Git changes synced for project: {project.name}")
        else:
            self.logger.info(f"No changes to publish for project: {project.name}")

    def _generate_readme(self, project: Project):

        try:
            project.media[Media.IMAGES.TYPE] = project.local.get_media_files(Media.IMAGES.TYPE)

            readme_template = self.tp.env.get_template('github/README.md')
            readme = readme_template.render(project)

            self.logger.info(f"Generated GitHub readme for {project.name}")
            return readme

        except Exception as e:
            self.logger.error(f"Failed to generate GitHub readme for {project.name}: {e}")
            raise