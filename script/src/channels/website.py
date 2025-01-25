import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict

import yaml

from script.src.channels._channel import Channel
from script.src.config import Config
from script.src.constants import MEDIA_TYPES, Extensions, Files, Status
from script.src.utils import (
    get_project_metadata,
    get_project_path,
    is_public_github_repo,
)


class WebsiteHandler(Channel):

    def __init__(self, config: Config):
        super().__init__(__name__, self.__class__.__name__, config)

    def publish(self) -> None:
        os.chdir(self.config.jekyll_dir)
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        
        if result.stdout.strip():
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', 'Publishing staged files'], check=True)
            subprocess.run(['git', 'push', 'origin', 'main'], check=True)
            self.logger.info("Published Jekyll site changes")
        else:
            self.logger.info("No changes to publish for website")

    def stage(self, name: str) -> None:
       
        metadata = get_project_metadata(self, name)
        status = metadata['project']['status']

        if status != Status.COMPLETE:
            self.logger.warning(f"{name} status is not complete. Skipping staging.")
            return

        self.logger.info(f"Staging website for {name}")

        self.stage_media(name)
        
        post = self.generate_post(name)
        post_date = metadata['project']['date_created']
        post_path = self.config.website_posts_dir / f"{post_date}-{name}.md"
        with open(post_path, 'w') as f:
            f.write(post)

        roadmap = self.generate_roadmap()
        with open(self.config.website_pages_dir / 'roadmap.md', 'w') as f:
            f.write(roadmap)
        
        self.logger.info(f"Successfully website post for {name}")

    def generate_post(self, name) -> None:
        self.logger.info(f"Staging post for {name}")
        try:
            metadata = get_project_metadata(self, name)
            template_path = "html/post.html"

            context = {
                'is_public_github_repo': is_public_github_repo(self, name),
                'images': self.tp.get_media_files(name, Extensions.IMAGE),
                'videos': self.tp.get_media_files(name, Extensions.VIDEO),
                'models': self.tp.get_media_files(name, Extensions.MODEL),
                'audio': self.tp.get_media_files(name, Extensions.AUDIO),
            }
            
            rendered_content = self.tp.process_template(name, template_path, context)

            front_matter = {
                'layout': 'post',
                'title': metadata['project']['title'],
                'description': metadata['project']['description'],
                'date': metadata['project']['date_created'],
                'tags': metadata['project']['tags'],
            } | self.determine_featured_content(name)

            return f"---\n{yaml.dump(front_matter, default_flow_style=False, sort_keys=False, allow_unicode=True)}---\n{rendered_content}"
        except Exception as e:
            self.logger.error(f"Failed to generate post for {name}: {e}")
            raise

    def determine_featured_content(self, name) -> Dict:
        metadata = get_project_metadata(self, name)
        project_dir = get_project_path(self, name)

        featured_content = metadata['project']['featured_content']
        if featured_content.get('type') == 'code':            
            source_file = Path(project_dir) / Path(featured_content['source'])
            if source_file.exists():
                with open(source_file, 'r') as f:
                    lines = f.readlines()
                    start = featured_content.get('start_line')
                    end = featured_content.get('end_line')
                    code_snippet = ''.join(lines[start:end])

                return {
                    'featured_code': code_snippet,
                    'code_language': featured_content.get('language')
                }
        else:
            return {
                'image': f"/media/{name}/images/{featured_content['source']}"
            }

    def generate_roadmap(self) -> None:
        self.logger.info("Staging roadmap")
        try:
            projects = []
            for item in self.config.base_dir.iterdir():
                if item.is_dir() and (item / Files.METADATA).exists():
                    projects.append(item.name)
            in_progress = []
            backlog = []
            public_repos = []

            for name in projects:

                metadata = get_project_metadata(self, name)
                project = metadata['project']
                name = metadata['project']['name']

                if is_public_github_repo(self, name):
                    public_repos.append(name)

                if project['status'] == Status.IN_PROGRESS:
                    in_progress.append(project)
                elif project['status'] == Status.BACKLOG:
                    backlog.append(project)

            backlog.sort(key=lambda x: x.get('priority', 0), reverse=True)

            context = {
                'in_progress': in_progress,
                'backlog': backlog,
                'public_repos': public_repos
            }

            return self.tp.process_template(name, 'md/roadmap.md', context)
        except Exception as e:
            self.logger.error(f"Failed to generate roadmap for {name}: {e}")
            raise

    def stage_media(self, name: str) -> None:
        self.logger.info(f"Staging media for {name}")

        try:
            source_dir = get_project_path(self, name) / 'media'
            dest_dir = self.config.website_media_dir / name

            if not source_dir.exists():
                return
                
            # Create destination directories
            for media_type in MEDIA_TYPES:
                (dest_dir / media_type).mkdir(parents=True, exist_ok=True)
                
                # Copy files
                source_type_dir = source_dir / media_type
                if source_type_dir.exists():
                    for file in source_type_dir.iterdir():
                        if file.is_file():
                            shutil.copy2(file, dest_dir / media_type / file.name)

            self.logger.info("Successfully staged media files")
        except Exception as e:
            self.logger.error(f"Failed to stage media for {name}: {e}")
            raise

    def rename(self, old_name: str, new_name: str) -> None:
        """Update all Jekyll-related files when renaming a project"""
        try:
            # Remove post file in _posts directory (will be recreated)
            jekyll_posts_dir = self.jekyll_posts_dir
            for post_file in jekyll_posts_dir.glob(f'*-{old_name}.md'):
                post_file.unlink()

            # Rename media directory
            old_media_dir = self.jekyll_media_dir / old_name
            if old_media_dir.exists():
                new_media_dir = self.jekyll_media_dir / new_name
                # Create parent directories if they don't exist
                new_media_dir.parent.mkdir(parents=True, exist_ok=True)
                old_media_dir.rename(new_media_dir)
                self.logger.info(f"Renamed media directory from {old_name} to {new_name}")

        except Exception as e:
            self.logger.error(f"Failed to rename Jekyll files: {e}")
            raise
