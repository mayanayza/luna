import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict

import yaml

from script.src.channels._channel import Channel
from script.src.config import Config
from script.src.constants import Media, Status
from script.src.utils import (
    get_media_files,
    get_project_metadata,
    get_project_path,
    is_project,
)


class WebsiteHandler(Channel):

    def __init__(self, config: Config):
        init = {
            'name': __name__,
            'class_name':self.__class__.__name__,
            'config': config
        }
            
        super().__init__(**init)

        self.media = {
           Media.IMAGES.TYPE: Media.IMAGES.EXT,
           Media.VIDEOS.TYPE: Media.VIDEOS.EXT,
           Media.MODELS.TYPE: Media.MODELS.EXT,
        }

    def publish(self, commit_message) -> None:
        try:
            os.chdir(self.config.website_dir)
            result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
            
            if result.stdout.strip():
                subprocess.run(['git', 'add', '.'], check=True)
                subprocess.run(['git', 'commit', '-m', commit_message], check=True)
                subprocess.run(['git', 'push', 'origin', 'main'], check=True)
                self.logger.info("Published website changes")
            else:
                self.logger.info("No changes to publish for website")
        except Exception as e:
            self.logger.error(f"Failed to publish website: {e}")
            raise

    def stage(self, name: str) -> str:
       
        try:
            metadata = get_project_metadata(self, name)
            status = metadata['project']['status']

            if status != Status.COMPLETE:
                self.logger.warning(f"{name} status is not complete. Skipping staging.")
                return ''
                
            self.stage_media(name)
            
            post = self.generate_post(name)
            post_date = metadata['project']['date_created']
            post_path = self.config.website_posts_dir / f"{post_date}-{name}.md"
            with open(post_path, 'w') as f:
                f.write(post)

            if self.config.enable_roadmap:
                roadmap = self.generate_roadmap()
                with open(self.config.website_pages_dir / 'roadmap.md', 'w') as f:
                    f.write(roadmap)
            self.logger.info(f"Successfully staged website content for {name}")

            return name
        except Exception as e:
            self.logger.error(f"Failed to stage website content for {name}: {e}")
            raise

    def generate_post(self, name) -> None:
        try:
            metadata = get_project_metadata(self, name)
            template_path = "html/post.html"

            context = {}
            for media_type in self.media:
                context[media_type] = get_media_files(self, name, media_type)
            
            rendered_content = self.tp.process_template(name, template_path, context)

            front_matter = {
                'layout': 'post',
                'title': metadata['project']['title'],
                'description': metadata['project']['description'],
                'date': metadata['project']['date_created'],
                'tags': metadata['project']['tags'],
            } | self.determine_featured_content(name)

            post = f"---\n{yaml.dump(front_matter, default_flow_style=False, sort_keys=False, allow_unicode=True)}---\n{rendered_content}"
            self.logger.info(f"Successfully generated post for {name}")
            return post
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
        try:
            projects = []
            for item in self.config.base_dir.iterdir():
                if is_project(self, item):
                    projects.append(item.name)
            in_progress = []
            backlog = []
            public_repos = []

            for name in projects:

                metadata = get_project_metadata(self, name)
                project = metadata['project']
                name = metadata['project']['name']

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

            roadmap = self.tp.process_template(name, 'md/roadmap.md', context)
            self.logger.info("Generated roadmap")
            return roadmap
        except Exception as e:
            self.logger.error(f"Failed to generate roadmap for {name}: {e}")
            raise

    def stage_media(self, name: str) -> None:
        try:
            output_dir = self.config.website_media_dir / name
                
            for media_type in self.media:
                media_files = get_media_files(self, name, media_type)
                output_type_dir = output_dir / str(media_type)
                output_type_dir.mkdir(parents=True, exist_ok=True)

                for file in media_files:
                    shutil.copy2(file, str(output_dir / media_type / file.name))

            self.logger.info(f"Successfully staged website media files for {name}")
        except Exception as e:
            self.logger.error(f"Failed to stage media for {name}: {e}")
            raise

    def rename(self, old_name: str, new_name: str) -> None:
        """Update all website-related files when renaming a project"""
        try:
            # Remove post file in _posts directory (will be recreated)
            self.delete(old_name)

            # Rename media directory
            old_media_dir = self.config.website_media_dir / old_name
            if old_media_dir.exists():
                new_media_dir = self.config.website_media_dir / new_name
                # Create parent directories if they don't exist
                new_media_dir.parent.mkdir(parents=True, exist_ok=True)
                old_media_dir.rename(new_media_dir)
                self.logger.info(f"Renamed website files from {old_name} to {new_name}")

        except Exception as e:
            self.logger.error(f"Failed to rename website files for {old_name}: {e}")
            raise

    def delete(self, name: str) -> None:
        try:
            website_posts_dir = self.config.website_posts_dir
            for post_file in website_posts_dir.glob(f'*-{name}.md'):
                post_file.unlink()
            media_dir = self.config.website_media_dir / name
            if media_dir.exists():
                shutil.rmtree(self.config.website_media_dir / name)
            self.logger.info(f"Deleted website files for {name}")
        except Exception as e:
            self.logger.error(f"Failed to delete website files for {name}: {e}")
            raise

