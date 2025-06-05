import shutil
from pathlib import Path

from PyPDF2 import PdfMerger
from weasyprint import HTML

from src.script.constants import Media
from src.script.integration._integration import Integration
from src.script.integration._registry import IntegrationRegistry
from src.script.project._project import Project
from utils import (
    format_name,
    get_image_dimensions,
    load_personal_info,
    resize_image_file,
)


class PDFIntegration(Integration):
    def __init__(self, registry: IntegrationRegistry):
        config = {
            'name': 'pdf',
            'env': {},
            'project_fields':{},
            'handlers':{
                'stage':[
                    {
                        'function': self.stage_project,
                        'scope': 'project'
                    },
                    {
                        'function': self.stage_cover,
                        'scope': 'global'
                    },
                ],
                'publish':[{
                    'function': self.publish,
                    'scope': 'global'
                }]
            },
            'apis':{
                'cli': self.cli
            }
        }

        self._staged_projects = []
            
        super().__init__(config, registry)

    def cli(self):
        self.registry.apis.get('cli').parser.add_argument('--collate-images', '-ci', action='store_true', help='Collate images for PDF publication')
        self.registry.apis.get('cli').parser.add_argument('--submission-name', '-sn', help='Name of what pdf is being submitted to')
        self.registry.apis.get('cli').parser.add_argument('--max-width', '-mw', help='Max width for images when generating separate image files for PDF publication')
        self.registry.apis.get('cli').parser.add_argument('--max-height', '-mh', help='Max height for images when generating separate image files for PDF publication')
        self.registry.apis.get('cli').parser.add_argument('--filename-prepend', '-fp', default='', help='Prepend string for PDF filename')

    def publish(self, **kwargs) -> None:
        # Search recursively for temp_pdf folders
        local = self.registry.get_integration('local')
        base_dir = local.base_dir
        temp_pdf_folders = list(Path(base_dir).rglob('temp_pdf'))
        output_folder = Path(base_dir / '_output')

        submission_name = kwargs.get('submission_name', '')
        
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

        self._staged_projects = []
    
    def stage_cover(self, **kwargs):

        submission_name = kwargs.get('submission_name', '')

        context = load_personal_info(self)
        projects = self._staged_projects
        context = context | {
            'projects': projects,
            'website': self.registry.website.base_url,
            'website_links': f"{self.registry.website.base_url}/links",
            'submission_name': submission_name
        }

        cover_template = self.tp.env.get_template('pdf/cover.html')
        html_string = cover_template.render(context)

        pdf = HTML(string=html_string).render()
        output_path = Path(self.config.base_dir / '_output' / '_cover.pdf')
        pdf.write_pdf(output_path)
            
    def stage_project(self, project: Project, **kwargs):
        """Generate PDF with optional image collation."""

        collate_images = kwargs.get('collate_images', False)
        max_width = kwargs.get('max_width', 1600)
        max_height = kwargs.get('max_height', 1200)
        filename_prepend = kwargs.get('filename_prepend', '')

        if max_width and isinstance(max_width, str) and max_width.isdigit():
            max_width = int(max_width)
        else:
            max_width = 1600
            
        if max_height and isinstance(max_height, str) and max_height.isdigit():
            max_height = int(max_height)
        else:
            max_height = 1200

        temp_dir = project.local.base_dir / 'temp_pdf'
        Path(temp_dir).mkdir(exist_ok=True)

        image_pdfs = []
        context = {}
        images = project.local.get_media_files(Media.IMAGES.TYPE)
        if collate_images:
            image_pdfs = self._generate_images_pdf(project, images)
        else:
            context['image_file_names'] = self._stage_images(project, images, max_width, max_height, filename_prepend)
        if project.media['featured_content']['type'] == 'image':
            context['featured_image'] = str((project.local.project_path / 'media' / project.media['featured_content']['source']).absolute())

        context['has_non_image_media'] = self._has_non_image_media_files(project)
        context = context | project.get_all_data()
        # Generate main content PDF

        project_template = self.tp.env.get_template('pdf/project.html')
        html_string = project_template.render(context)
        main_pdf = HTML(string=html_string, base_url=project.local.project_path).render()
        # Combine main content with image pages
        all_pages = main_pdf.pages + image_pdfs
        output_pdf = main_pdf.copy(all_pages)
        output_path = temp_dir / f"{project.name}.pdf"
        output_pdf.write_pdf(output_path)

        self._staged_projects.append(project.metadata['title'])

    def _has_non_image_media_files(self, project: Project):
        videos = len( project.local.get_media_files(Media.VIDEOS.TYPE) ) > 0
        audios = len( project.local.get_media_files(Media.AUDIO.TYPE) ) > 0
        models = len( project.local.get_media_files(Media.MODELS.TYPE) ) > 0
        embeds = len( project.media['embeds'] ) > 0
        return videos or audios or embeds or models

    def _generate_images_pdf(self, project: Project, images, images_per_page=2):
        try:
            images = sorted(images)

            image_groups = self._process_images(images, images_per_page)
                
            context = project.process_metadata() | {
                'image_groups': image_groups,
                'title': project.metadata['title']
            }
            
            images_template = self.tp.env.get_template('pdf/project_images.html')
            html_string = images_template.render(context)

            image_pdf = HTML(string=html_string, base_url=project.local.project_path).render()
            
            self.logger.info(f"Generated image PDFs for {project.name} with {images_per_page} images per page")
            return image_pdf.pages
            
        except Exception as e:
            self.logger.error(f"Failed to generate image PDF for {project.name}: {e}")
            raise
            
    def _process_images(self, images, images_per_page=2):
    
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

    def _stage_images(self, project: Project, images, max_width, max_height, filename_prepend):
        try:
            temp_dir = project.local.project_path / 'temp_pdf'
            Path(temp_dir).mkdir(exist_ok=True)
            
            counter = 1
            new_names = []
            
            for file in sorted(images):
                temp_file = resize_image_file(self, file, max_width, max_height)
                new_name = f"{project.name}_{counter}{file.suffix}"
                if filename_prepend:
                    new_name = f"{filename_prepend}_{new_name}"
                new_names.append(new_name)
                shutil.copy(str(temp_file), str(temp_dir / new_name))
                temp_file.unlink()
                counter += 1
            self.logger.info(f"Staged images for {project.name}")
            return ", ".join(new_names)
        except Exception as e:
            self.logger.error(f"Failed stage images for {project.name}: {e}")
            raise