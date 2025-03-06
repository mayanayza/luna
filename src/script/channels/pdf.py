import shutil
from pathlib import Path

from PyPDF2 import PdfMerger
from weasyprint import HTML

from src.script.channels._channel import Channel
from src.script.config import Config
from src.script.constants import Media
from src.script.utils import (
    format_name,
    get_image_dimensions,
    get_project_media_files,
    get_project_metadata,
    get_project_path,
    get_website_media_files,
    load_personal_info,
    resize_image_file,
)


class PDFHandler(Channel):
    def __init__(self, config: Config):
        init = {
            'name': __name__,
            'class_name':self.__class__.__name__,
            'config': config
        }
            
        super().__init__(**init)

    def get_commands(self):
        """Return commands supported by PDF handler"""
        return {
            'publish': self.handle_publish,
        }
        
    def handle_publish(self, **kwargs):
        """Handle publish command for PDF generation"""
        projects = self.validate_projects(kwargs.get('projects', []))
        
        if not projects:
            self.logger.error("No valid projects provided for PDF generation")
            return
            
        # Extract parameters
        collate_images = kwargs.get('collate_images', False)
        max_width = kwargs.get('max_width', 1600)
        max_height = kwargs.get('max_height', 1200)
        filename_prepend = kwargs.get('filename_prepend', '')
        submission_name = kwargs.get('submission_name', '')
        
        # Set default values if needed
        if max_width and isinstance(max_width, str) and max_width.isdigit():
            max_width = int(max_width)
        else:
            max_width = 1600
            
        if max_height and isinstance(max_height, str) and max_height.isdigit():
            max_height = int(max_height)
        else:
            max_height = 1200
            
        # Generate PDFs for each project
        for name in projects:
            try:
                self.stage_projects(name, max_width, max_height, filename_prepend, collate_images)
            except Exception as e:
                self.logger.error(f"Failed to generate PDF for {name}: {e}")
                
        # Generate cover and publish final PDF
        try:
            self.stage_cover(projects, submission_name)
            self.publish(submission_name)
        except Exception as e:
            self.logger.error(f"Failed to publish final PDF: {e}")

    def publish(self, submission_name='') -> None:
        # Search recursively for temp_pdf folders
        temp_pdf_folders = list(Path(self.config.base_dir).rglob('temp_pdf'))
        output_folder = Path(self.config.base_dir / '_output')
        
        try:
            # Create output folder if it doesn't exist
            output_folder.mkdir(exist_ok=True)
            
            # First, process temp folders
            for temp_folder in temp_pdf_folders:
                # Move PDFs
                for pdf_file in temp_folder.glob('*.pdf'):
                    shutil.move(str(pdf_file), str(output_folder / pdf_file.name))
                
                # Move images
                for extension in Media.get_extensions(Media.IMAGES.TYPE):
                    for image_file in temp_folder.glob(extension):
                        shutil.move(str(image_file), str(output_folder / image_file.name))
                
                # Delete temp folder and its contents
                shutil.rmtree(temp_folder)
                self.logger.info(f"Processed and removed {temp_folder}")

            # Check for PDFs in the output folder
            pdf_files = list(output_folder.glob('*.pdf'))
            if not pdf_files:
                self.logger.warning("No PDF files found in output folder.")
                return
                
            # Separate cover from other PDFs
            not_cover = [p for p in pdf_files if p.name != '_cover.pdf']
            cover_files = [p for p in pdf_files if p.name == '_cover.pdf']
            
            # Handle case when cover file might not exist
            if cover_files:
                pdf_files = cover_files + not_cover
            else:
                self.logger.warning("No cover PDF found, proceeding without it.")
                pdf_files = not_cover
                
            if not pdf_files:
                self.logger.warning("No valid PDF files to merge.")
                return
                
            # Create merger
            merger = PdfMerger()
            
            # Add each PDF to the merger
            for pdf in pdf_files:
                try:
                    merger.append(str(pdf))
                except Exception as e:
                    self.logger.error(f"Error adding PDF {pdf.name} to merger: {e}")
                    # Continue with other PDFs
            
            # Get personal info for filename
            try:
                personal_info = load_personal_info(self)
                first_name = personal_info.get('first_name', '')
                last_name = personal_info.get('last_name', '')
                name = f"{first_name}-{last_name}"
            except Exception as e:
                self.logger.error(f"Error loading personal info: {e}")
                name = "User"
            
            # Generate output filename
            if submission_name:
                try:
                    file_name, _ = format_name(self, submission_name)
                    file_name = f"{name}-{file_name}"
                except Exception as e:
                    self.logger.error(f"Error formatting submission name: {e}")
                    file_name = f"{name}-submission"
            else:
                file_name = f"{name}-submission"

            # Write combined PDF
            try:
                combined_path = output_folder / f"{file_name}.pdf"
                merger.write(str(combined_path))
                merger.close()
                
                # Delete source PDFs only after successful write
                for pdf in pdf_files:
                    try:
                        pdf.unlink()
                    except Exception as e:
                        self.logger.warning(f"Could not delete source PDF {pdf.name}: {e}")
                
                self.logger.info(f"Published PDF at {combined_path}")
            except Exception as e:
                self.logger.error(f"Error writing combined PDF: {e}")
                raise
        except Exception as e:
            self.logger.error(f"Error publishing PDF: {e}")
            raise
    
    def stage_cover(self, projects, submission_name):
        context = load_personal_info(self)
        projects = [get_project_metadata(self, p)['project']['title'] for p in projects]
        context = context | {
            'projects': projects,
            'website': self.config.website_domain,
            'website_links': f"{self.config.website_domain}/links",
            'submission_name': submission_name
        }
        html_string = self.tp.process_pdf_cover_template(context)
        pdf = HTML(string=html_string).render()
        output_path = Path(self.config.base_dir / '_output' / '_cover.pdf')
        pdf.write_pdf(output_path)
            
    def stage_projects(self, name, max_width, max_height, filename_prepend, collate_images):
        """Generate PDF with optional image collation."""

        try:
            project_dir = get_project_path(self, name)
            metadata = self.tp.process_project_metadata(name)
            temp_dir = project_dir / 'temp_pdf'
            Path(temp_dir).mkdir(exist_ok=True)

            image_pdfs = []
            context = {}
            images = get_project_media_files(self, name, Media.IMAGES.TYPE)
            if collate_images:
                image_pdfs = self.generate_images_pdf(name, images)
            else:
                context['image_file_names'] = self.stage_images(name, images, max_width, max_height, filename_prepend)
            if metadata['project']['featured_content']['type'] == 'image':
                context['featured_image'] = str((project_dir / 'media' / metadata['project']['featured_content']['source']).absolute())

            metadata['project']['has_non_image_media'] = self.has_non_image_media_files(name)
            context = context | metadata
            # Generate main content PDF
            html_string = self.tp.process_pdf_project_template(name, context)
            main_pdf = HTML(string=html_string, base_url=project_dir).render()
            # Combine main content with image pages
            all_pages = main_pdf.pages + image_pdfs
            output_pdf = main_pdf.copy(all_pages)
            output_path = temp_dir / f"{name}.pdf"
            output_pdf.write_pdf(output_path)

            self.logger.info(f"Generated PDF for {name}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate PDF for {name}: {e}")
            raise

    def has_non_image_media_files(self, name):
        metadata = get_project_metadata(self)
        videos = len( get_website_media_files(self, name, Media.VIDEOS.TYPE) ) > 0
        audios = len( get_website_media_files(self, name, Media.AUDIO.TYPE) ) > 0
        models = len( get_website_media_files(self, name, Media.MODELS.TYPE) ) > 0
        embeds = len(metadata['project']['embeds']) > 0
        return videos or audios or embeds or models


    def generate_images_pdf(self, name, images, images_per_page=2):
        try:
            project_dir = get_project_path(self, name)
            metadata = get_project_metadata(self, name)
            images = sorted(images)

            image_groups = self.process_images(images, images_per_page)
                
            context = self.tp.process_project_metadata(name) | {
                'image_groups': image_groups,
                'title': metadata['project']['title']
            }
            
            html_string = self.tp.process_pdf_images_template(name, context)
            image_pdf = HTML(string=html_string, base_url=project_dir).render()
            
            self.logger.info(f"Generated image PDFs for {name} with {images_per_page} images per page")
            return image_pdf.pages
            
        except Exception as e:
            self.logger.error(f"Failed to generate image PDF for {name}: {e}")
            raise
            
    def process_images(self, images, images_per_page=2):
    
        landscape_dims = {
            'max_width': 1600,
            'max_height': 1000
        }
        portrait_dims = {
            'max_width': 1000,
            'max_height': 1400
        }

        # First, separate images by orientation
        landscape_images = []
        portrait_images = []
        
        for img in images:
            width, height = get_image_dimensions(self, img)
            if width > height:
                landscape_images.append(img)
            else:
                portrait_images.append(img)
        
        image_groups = []
        
        # Process landscape images
        for i in range(0, len(landscape_images), images_per_page):
            group_images = landscape_images[i:i + images_per_page]
            processed_images = [
                resize_image_file(self, img, **landscape_dims).resolve()
                for img in group_images
            ]
            image_groups.append({
                'images': processed_images,
                'layout': 'vertical'
            })
        
        # Process portrait images
        for i in range(0, len(portrait_images), images_per_page):
            group_images = portrait_images[i:i + images_per_page]
            processed_images = [
                resize_image_file(
                    self,
                    img,
                    max_width=portrait_dims['max_width'] // 2,
                    max_height=portrait_dims['max_height']
                ).resolve()
                for img in group_images
            ]
            image_groups.append({
                'images': processed_images,
                'layout': 'horizontal'
            })
        
        return image_groups

    def stage_images(self, name, images, max_width, max_height, filename_prepend):
        try:
            project_dir = get_project_path(self, name)
            temp_dir = project_dir / 'temp_pdf'
            Path(temp_dir).mkdir(exist_ok=True)
            
            counter = 1
            new_names = []
            
            for file in sorted(images):
                temp_file = resize_image_file(self, file, max_width, max_height)
                new_name = f"{name}_{counter}{file.suffix}"
                if filename_prepend:
                    new_name = f"{filename_prepend}_{new_name}"
                new_names.append(new_name)
                shutil.copy(str(temp_file), str(temp_dir / new_name))
                temp_file.unlink()
                counter += 1
            self.logger.info(f"Staged images for {name}")
            return ", ".join(new_names)
        except Exception as e:
            self.logger.error(f"Failed stage images for {name}: {e}")
            raise