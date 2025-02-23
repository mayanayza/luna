import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Literal

import numpy as np
import trimesh
import yaml
from moviepy import VideoFileClip
from PIL import Image

from src.script.constants import Files, Media


def setup_logging(name: str):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    return logging.getLogger(name)

def strip_emoji(text: str) -> str:
    """Remove emoji characters from text"""
    emoji_pattern = re.compile("[\U0001F000-\U0001F6FF]|[\U0001F900-\U0001F9FF]|[\u2600-\u26FF]|[\u2700-\u27BF]|[\uFE00-\uFE0F]")
    return emoji_pattern.sub('', text).strip()

def format_name(self, display_name: str) -> str:
    # Remove emoji and other special characters, convert to lowercase
    title = strip_emoji(display_name)
    title = re.sub(r'[^a-zA-Z0-9\s-]', '', title)
    
    # Convert to kebab-case
    name = title.strip().lower().replace(' ', '-')
    name = re.sub(r'-+', '-', name)
    
    return name, title

def load_template(self, template_name: str) -> str:
    """Load a template file and return its contents"""
    script_dir = Path(__file__).resolve().parent
    templates_dir = script_dir.parent / 'templates'
    template_path = templates_dir / template_name
    try:
        with open(template_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        self.logger.error(f"Template file not found: {template_path}")
        raise

def load_personal_info(self):
    script_dir = Path(__file__).resolve().parent.parent
    with open(script_dir / 'personal-info.yml', 'r') as f:
        return yaml.safe_load(f)


def is_public_github_repo(self, name) -> str:
    project_dir = get_project_path(self, name)
    os.chdir(project_dir)
    visibility = subprocess.run(['gh', 'repo', 'view', '--json', 'visibility', '-q', '.visibility'], capture_output=True, text=True)
    visibility = visibility.stdout.strip().upper()
    if visibility == 'PUBLIC':
        return True
    else:
        return False

def is_project(self, item) -> bool:
    return item.is_dir() and (item / 'content' / Files.METADATA).exists()

def get_project_media_files(self, name, type):
    project_dir = get_project_path(self, name)
    media_path = project_dir / 'media' / type
    extensions = Media.get_extensions(type)
    files = []
    if media_path.exists():
        for ext in extensions:
            files.extend(list(media_path.glob(ext)))
    return files

def get_website_media_files(self, name, type):
    website_media_dir = self.config.website_media_dir / name / type
    media_files = []

    for file in website_media_dir.iterdir():
        media_files.append(f"/media/{name}/{type}/{file.name}")

    return sorted(media_files)

def get_project_metadata(self, name: str) -> yaml:
    project_dir = get_project_path(self, name)
    with open(project_dir / 'content' / Files.METADATA, 'r') as f:
        return yaml.safe_load(f)

def get_project_content(self, name: str) -> str:
    project_dir = get_project_path(self, name)
    with open(project_dir / 'content' / Files.CONTENT, 'r') as f:
        return f.read()

def get_project_readme(self, name: str) -> str:
    project_dir = get_project_path(self, name)
    with open(project_dir / 'content' / Files.README, 'r') as f:
        return f.read()

def get_project_path(self, name: str) -> Path:
    return self.config.base_dir / name

def convert_model_file(self, model_file, output_format: Literal['glb']='glb'):
    try:
        # Load the STL file
        mesh = trimesh.load(model_file)
        mesh.visual.face_colors = [232,170,191]

        rotation_matrix = trimesh.transformations.rotation_matrix(
            angle=np.radians(-90),
            direction=[1, 0, 0]
        )

        mesh.apply_transform(rotation_matrix)
                
        # Create a scene with the mesh
        scene = trimesh.Scene(mesh)
        
        scene.lights = {
            'directional_1': {
                'color': [1.0, 1.0, 1.0],
                'direction': [0, 0, -1],
                'intensity': 1.0
            },
            'point_1': {
                'color': [1.0, 0.9, 0.9],
                'position': [0, 0, 10],
                'intensity': 1.0,
                'range': 100
            }
        }

        # Create temp file with new extension
        temp_path = Path('temp') / f"{model_file.stem}.{output_format}"
        temp_path.parent.mkdir(exist_ok=True)  # Ensure temp directory exists
        
        # Export to temp file
        scene.export(str(temp_path), file_type=output_format)
        
        return temp_path
        
    except Exception as e:
        raise self.logger.error(f"Failed to convert model: {str(e)}")

def convert_video_file(self, video_file, output_format: Literal['mp4', 'webm'] = 'mp4'):
    try:
        video = VideoFileClip(video_file)
        # Create temp file with new extension
        temp_path = Path('temp') / f"{video_file.stem}.{output_format}"
        temp_path.parent.mkdir(exist_ok=True)  # Ensure temp directory exists
        
        if output_format == 'mp4':
            video.write_videofile(
                str(temp_path),
                codec='libx264',
                audio_codec='aac',
                ffmpeg_params=[
                    '-profile:v', 'baseline',
                    '-level', '3.0',
                    '-movflags', '+faststart',
                    '-pix_fmt', 'yuv420p'
                ]
            )
        else:  # webm
            video.write_videofile(
                str(temp_path),
                codec='libvpx',
                audio_codec='libvorbis'
            )
        
        video.close()
        return temp_path
    except Exception as e:
        raise self.logger.error(f"Failed to convert video: {str(e)}")


def get_image_dimensions(self, image_path):
    from PIL import Image
    
    with Image.open(image_path) as img:
        return img.size

def resize_image_file(self, image_file, max_width: int=-1, max_height: int=-1):
        
    with Image.open(image_file) as img:
        # Get original dimensions
        width, height = img.size
        width_ratio = 1 if max_width == -1 else max_width / width
        height_ratio = 1 if max_height == -1 else max_height / height
        
        # Use the smaller ratio to ensure both dimensions fit within maximums
        scale_ratio = min(width_ratio, height_ratio)
        
        # Calculate new dimensions
        new_width = int(width * scale_ratio)
        new_height = int(height * scale_ratio)
                    
        # Resize the image
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create temp file with same name but in temp directory
        temp_path = Path('temp') / image_file.name
        temp_path.parent.mkdir(exist_ok=True)  # Ensure temp directory exists
        resized_img.save(temp_path)
        return temp_path