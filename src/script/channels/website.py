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
    convert_model_file,
    convert_video_file,
    get_project_content,
    get_project_media_files,
    get_project_metadata,
    get_project_path,
    is_project,
    load_personal_info,
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

        self.media = [
           Media.IMAGES,
           Media.VIDEOS,
           Media.MODELS,
           Media.EMBEDS
        ]

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
            embed_content = self.stage_embed_content(name)
            
            post = self.generate_post(name, embed_content)
            post_date = metadata['project']['date_created']
            post_path = self.config.website_posts_dir / f"{post_date}-{name}.md"
            with open(post_path, 'w') as f:
                f.write(post)

            self.logger.info(f"Successfully staged website content for {name}")

            return name
        except Exception as e:
            self.logger.error(f"Failed to stage website content for {name}: {e}")
            raise

    def stage_pages(self):

        metadatas = []
        for item in self.config.base_dir.iterdir():
            if is_project(self, item):
                metadata = self.tp.process_project_metadata(item.name)
                metadatas.append(metadata)

        roadmap = self.generate_roadmap_page(metadatas)
        with open(self.config.website_pages_dir / 'roadmap.md', 'w') as f:
            f.write(roadmap)

        links = self.generate_links_page(metadatas)
        with open(self.config.website_pages_dir / 'links.md', 'w') as f:
            f.write(links)

        about = self.generate_about_page()
        with open(self.config.website_pages_dir / 'about.md', 'w') as f:
            f.write(about)

    def generate_post(self, name, embed_content) -> None:
        try:
            metadata = get_project_metadata(self, name)            

            front_matter = {
                'layout': 'post',
                'title': metadata['project']['title'],
                'name' : metadata['project']['name'],
                'tagline': metadata['project']['tagline'],
                'date': metadata['project']['date_created'],
                'tags': metadata['project']['tags'],
                'featured': metadata['project']['feature_post'],
                'written_content': get_project_content(self, name),
                'images':self.get_website_media_files(name, Media.IMAGES.TYPE),
                'videos':self.get_website_media_files(name, Media.VIDEOS.TYPE),
                'models':self.get_website_media_files(name, Media.MODELS.TYPE),
            }
            front_matter = front_matter | embed_content 
            front_matter = front_matter | self.determine_featured_content(name)

            content = self.tp.get_post_template()

            post = f"---\n{yaml.dump(front_matter, default_flow_style=False, sort_keys=False, allow_unicode=True)}---\n{content}"
            self.logger.info(f"Successfully generated post for {name}")
            return post
        except Exception as e:
            self.logger.error(f"Failed to generate post for {name}: {e}")
            raise

    def generate_roadmap_page(self, metadatas) -> None:
        try:
            in_progress = []
            backlog = []
            complete_art = []
            complete_other = []

            for metadata in metadatas:

                project = metadata['project']

                if project['status'] == Status.IN_PROGRESS:
                    in_progress.append(project)
                elif project['status'] == Status.BACKLOG:
                    backlog.append(project)
                elif project['status'] == Status.COMPLETE:
                    if "Art" in project['tags']:
                        complete_art.append(project)
                    else:
                        complete_other.append(project)

            backlog.sort(key=lambda x: x.get('priority', 0), reverse=True)

            front_matter = {
                'in_progress': in_progress,
                'backlog': backlog,
                'complete_art': complete_art,
                'complete_other': complete_other,
                'title': "Roadmap",
                'permalink': '/roadmap/',
                'hide_header': False,
                'layout': 'page',
                'website': self.config.website_domain
            }

            content = self.tp.get_roadmap_template()

            roadmap = f"---\n{yaml.dump(front_matter, default_flow_style=False, sort_keys=False, allow_unicode=True)}---\n{content}"

            self.logger.info("Generated roadmap")
            return roadmap
        except Exception as e:
            self.logger.error(f"Failed to generate roadmap page: {e}")
            raise

    def generate_links_page(self, metadatas) -> None:
        try:
            featured = []
            in_progress = []

            for metadata in metadatas:

                project = metadata['project']
                name = project['name']

                if project['status'] == Status.IN_PROGRESS:
                    in_progress.append(project)

                if project['feature_post'] and project['status'] == Status.COMPLETE:

                    if project['featured_content']['type'] == 'image':
                        project = project | self.determine_featured_content(name)

                    featured.append(project)


            front_matter = {
                'in_progress': in_progress,
                'featured_projects': featured,
                'title': "Maya's Links",
                'permalink': '/links/',
                'hide_header': True,
                'layout': 'links',
                'website': self.config.website_domain
            }
                                    
            content = self.tp.get_links_template()

            links = f"---\n{yaml.dump(front_matter, default_flow_style=False, sort_keys=False, allow_unicode=True)}---\n{content}"

            self.logger.info("Generated links")
            return links
        except Exception as e:
            self.logger.error(f"Failed to generate links page: {e}")
            raise

    def generate_about_page(self):
        try:
            context = load_personal_info(self)
            about = self.tp.process_about_template(context) 
            self.logger.info("Generated about")
            return about
        except Exception as e:
            self.logger.error(f"Failed to generate about page: {e}")
            raise

    def stage_media(self, name: str) -> None:
        try:
            output_dir = self.config.website_media_dir / name
                
            for media in self.media:
                media_files = get_project_media_files(self, name, media.TYPE)

                output_type_dir = output_dir / str(media.TYPE)
                if output_type_dir.exists():
                    shutil.rmtree(output_type_dir)
                output_type_dir.mkdir(parents=True, exist_ok=True)

                if media_files:                    
                    for file in media_files:
                        file_name = str(file.name)

                        self.logger.info(f"staging {file_name}")

                        cleanup_source = True
                        
                        if media.TYPE == Media.IMAGES.TYPE:
                            source_file = resize_image_file(self, file, 1920, 1080)
                        elif media.TYPE == Media.VIDEOS.TYPE:
                            source_file = convert_video_file(self, file, 'mp4')
                        elif media.TYPE == Media.MODELS.TYPE:
                            source_file = convert_model_file(self, file, 'glb')
                        else:
                            source_file = file
                            cleanup_source = False
                        
                        dest_path = output_type_dir / source_file.name
                        shutil.copy2(source_file, dest_path)
                        
                        if cleanup_source:
                            source_file.unlink()

                
            self.logger.info(f"Successfully staged all website media files for {name}")
        except Exception as e:
            self.logger.error(f"Failed to stage media for {name}: {e}")
            raise

    def stage_embed_content(self, name):
        try:
            metadata = get_project_metadata(self, name)
            project_dir = get_project_path(self, name)

            output_embed_dir = self.config.website_media_dir / name / Media.EMBEDS.TYPE

            embeds = {}

            for embed in metadata['project']['embeds']:
                source_file = Path(project_dir) / Path(embed['source'])
                dest_path =  output_embed_dir / Path(embed['source']).name
                embed_key = f"{embed['type']}_embeds"

                if embed_key not in embeds:
                    embeds[embed_key] = []

                embeds[embed_key].append(f"/media/name/{Media.EMBEDS.TYPE}/{Path(embed['source']).name}")

                shutil.copy2(source_file, dest_path)

            self.logger.info(f"Successfully staged all embed files for {name}")

            return embeds
        except Exception as e:
            self.logger.error(f"Failed to stage embed files for {name}: {e}")
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
                'featured_image': f"/media/{name}/{featured_content['source']}"
            }

    def get_website_media_files(self, name, type):
        website_media_dir = self.config.website_media_dir / name / type
        media_files = []

        for file in website_media_dir.iterdir():
            media_files.append(f"/media/{name}/{type}/{file.name}")

        return sorted(media_files)

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

