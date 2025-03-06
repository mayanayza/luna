import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

import yaml

from src.script.channels._channel import Channel
from src.script.config import Config
from src.script.constants import Media
from src.script.utils import (
    convert_model_file,
    convert_video_file,
    get_project_media_files,
    get_project_metadata,
    get_project_path,
    get_website_media_files,
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
        
    def get_commands(self):
        """Return commands supported by Website handler"""
        return {
            'stage': self.handle_stage,
            'publish': self.handle_publish,
        }
        
    def handle_stage(self, **kwargs):
        """Handle stage command for website content"""
        projects = self.validate_projects(kwargs.get('projects', []))
        staged_projects = self.stage_web(projects)
        return staged_projects
    
    def handle_publish(self, **kwargs):
        """Handle publish command for website content"""
        projects = self.validate_projects(kwargs.get('projects', []))
        commit_message = kwargs.get('commit_message', 'Update website content')
        self.publish_web(projects, commit_message)
        
    def stage_web(self, projects: List[str]) -> List[str]:
        """Stage website content for projects"""
        staged_projects = []
        for name in projects:
            try:
                result = self.stage_post(name)
                if result:
                    staged_projects.append(result)
            except Exception as e:
                self.logger.error(f"Failed to stage website content for {name}: {e}")

        try:
            self.stage_personal_info()
        except Exception as e:
            self.logger.error(f"Failed to stage personal info: {e}")

        return [p for p in staged_projects if p.strip()]
        
    def publish_web(self, projects: List[str], commit_message: str) -> None:
        """Publish website content for projects"""
        try:
            # First stage all content
            staged_projects = self.stage_web(projects)
            
            # Then publish changes
            if staged_projects:
                commit_msg = f"Updating content for {', '.join(staged_projects)}"
            else:
                commit_msg = commit_message
                
            self.publish(commit_msg)
        except Exception as e:
            self.logger.error(f"Failed to publish website: {e}")

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

    def stage(self, name: str) -> None:
        """Stage a single project's content (for compatibility with rename)"""
        try:
            self.stage_post(name)
            self.logger.info(f"Staged website content for {name}")
        except Exception as e:
            self.logger.error(f"Failed to stage website content for {name}: {e}")

    def stage_post(self, name: str) -> str:
       
        try:
            metadata = get_project_metadata(self, name)
                
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

    def stage_personal_info(self):
        info = load_personal_info(self)

        info.pop('last_name', None)
        info.pop('email', None)
        info.pop('phone', None)
        info.pop('location', None)

        info = yaml.dump(info, default_flow_style=False, sort_keys=False, allow_unicode=True)

        with open(self.config.website_data_dir / 'personal_info.yml', 'w') as f:
            f.write(info)

    def generate_post(self, name, embed_content) -> None:
        try:
            metadata = self.tp.process_project_metadata(name)            

            front_matter = {
                'layout': 'post',
                'date': metadata['project']['date_created'],
                'featured': metadata['project']['feature_post'],
                'images':get_website_media_files(self, name, Media.IMAGES.TYPE),
                'videos':get_website_media_files(self, name, Media.VIDEOS.TYPE),
                'models':get_website_media_files(self, name, Media.MODELS.TYPE),
            }
            front_matter = front_matter | metadata['project']
            front_matter = front_matter | embed_content 
            front_matter = front_matter | self.determine_featured_content(name)

            post_content = "{% include post-content.html %}"

            post = f"---\n{yaml.dump(front_matter, default_flow_style=False, sort_keys=False, allow_unicode=True)}---\n{post_content}"
            self.logger.info(f"Successfully generated post for {name}")
            return post
        except Exception as e:
            self.logger.error(f"Failed to generate post for {name}: {e}")
            raise

    def stage_media(self, name: str) -> None:
        try:
            output_dir = self.config.website_media_dir / name
                
            for media in [Media.IMAGES, Media.VIDEOS, Media.MODELS, Media.EMBEDS]:
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
                if embed['source'] and embed['type']:
                    source_file = Path(project_dir) / Path(embed['source'])
                    dest_path =  output_embed_dir / Path(embed['source']).name
                    embed_key = f"{embed['type']}_embeds"

                    if embed_key not in embeds:
                        embeds[embed_key] = []

                    embeds[embed_key].append(f"/media/{name}/{Media.EMBEDS.TYPE}/{Path(embed['source']).name}")

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