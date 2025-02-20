import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict

import yaml

from src.script.channels._channel import Channel
from src.script.config import Config
from src.script.constants import Media, Status
from src.script.utils import (
    get_media_files,
    get_project_metadata,
    get_project_path,
    is_project,
    resize_image_file,
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
           Media.VIDEOS.TYPE: ('*.webm',),
           Media.MODELS.TYPE: ('*.glb',),
           Media.EMBEDS.TYPE: Media.EMBEDS.EXT,
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

    def stage_post(self, name: str) -> str:
       
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

            self.logger.info(f"Successfully staged website content for {name}")

            return name
        except Exception as e:
            self.logger.error(f"Failed to stage website content for {name}: {e}")
            raise

    def stage_roadmap(self):
        if self.config.enable_roadmap:
            roadmap = self.generate_roadmap_page()
            with open(self.config.website_pages_dir / 'roadmap.md', 'w') as f:
                f.write(roadmap)

    def stage_links(self):
        links = self.generate_links_page()
        with open(self.config.website_pages_dir / 'links.md', 'w') as f:
                f.write(links)

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
                'tagline': metadata['project']['tagline'],
                'date': metadata['project']['date_created'],
                'tags': metadata['project']['tags'],
                'featured': metadata['project']['feature_post']
            } 
            front_matter = front_matter | self.determine_featured_content(name)
            front_matter = front_matter | self.generate_gallery(name)

            post = f"---\n{yaml.dump(front_matter, default_flow_style=False, sort_keys=False, allow_unicode=True)}---\n{rendered_content}"
            self.logger.info(f"Successfully generated post for {name}")
            return post
        except Exception as e:
            self.logger.error(f"Failed to generate post for {name}: {e}")
            raise

    def generate_gallery(self, name) -> Dict:
        website_image_dir = self.config.website_media_dir / name / Media.IMAGES.TYPE
        gallery_images = []

        for image in website_image_dir.iterdir():
            gallery_images.append(f"/media/{name}/{Media.IMAGES.TYPE}/{image.name}")

        return {
            'gallery_images':gallery_images
        }

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
                'image': f"/media/{name}/{featured_content['source']}"
            }

    def generate_roadmap_page(self) -> None:
        try:
            projects = []
            for item in self.config.base_dir.iterdir():
                if is_project(self, item):
                    projects.append(item.name)

            in_progress = []
            backlog = []
            complete = []

            for name in projects:

                metadata = self.tp.process_project_metadata(name)
                project = metadata['project']

                if project['status'] == Status.IN_PROGRESS:
                    in_progress.append(project)
                elif project['status'] == Status.BACKLOG:
                    backlog.append(project)
                elif project['status'] == Status.COMPLETE:
                    complete.append(project)

            backlog.sort(key=lambda x: x.get('priority', 0), reverse=True)

            context = {
                'in_progress': in_progress,
                'backlog': backlog,
                'complete': complete,
            }

            roadmap = self.tp.process_roadmap_template(context)
            self.logger.info("Generated roadmap")
            return roadmap
        except Exception as e:
            self.logger.error(f"Failed to generate roadmap page: {e}")
            raise

    def generate_links_page(self) -> None:
        try:
            projects = []
            for item in self.config.base_dir.iterdir():
                if is_project(self, item):
                    projects.append(item.name)

            featured = []
            in_progress = []

            for name in projects:

                metadata = self.tp.process_project_metadata(name)
                project = metadata['project']

                if project['status'] == Status.IN_PROGRESS:
                    in_progress.append(project)

                if project['feature_post'] and project['status'] == Status.COMPLETE:

                    if project['featured_content']['type'] == 'image':
                        project = project | self.determine_featured_content(name)

                    self.logger.info(project)

                    featured.append(project)

            context = {
                'featured': featured,
                'in_progress': in_progress
            }
                        
            links = self.tp.process_links_template(context)
            self.logger.info("Generated links")
            return links
        except Exception as e:
            self.logger.error(f"Failed to generate links page: {e}")
            raise

    def stage_media(self, name: str) -> None:
        try:
            output_dir = self.config.website_media_dir / name
            metadata = get_project_metadata(self, name)
            project_dir = get_project_path(self, name)
                
            for media_type in self.media:
                media_files = get_media_files(self, name, media_type)

                if media_files:
                    output_type_dir = output_dir / str(media_type)
                    if output_type_dir.exists():
                        shutil.rmtree(output_type_dir)
                    output_type_dir.mkdir(parents=True, exist_ok=True)

                    if media_type == Media.EMBEDS.TYPE:
                        for embed in metadata['project']['embeds']:
                            source_file = Path(project_dir) / Path(embed['source'])
                            embed_type_dir = output_type_dir / embed['type']
                            embed_type_dir.mkdir(exist_ok=True)
                            dest_path =  embed_type_dir / Path(embed['source']).name
                            shutil.copy2(source_file, dest_path)
                    
                    for file in media_files:
                        file_name = str(file.name)
                        
                        if media_type == Media.IMAGES.TYPE:
                            resized_image = resize_image_file(file.absolute(), 1920, 1080)
                            temp_path = file.parent / f"resized_{file_name}"
                            resized_image.save(temp_path)
                            source_file = temp_path
                        else:
                            source_file = file
                        
                        dest_path = output_type_dir / file_name
                        shutil.copy2(source_file, dest_path)
                        
                        if media_type == Media.IMAGES.TYPE:
                            temp_path.unlink()
                
            self.logger.info(f"Successfully staged all website media files for {name}")
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

