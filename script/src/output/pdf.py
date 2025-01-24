import shutil
from pathlib import Path

import markdown
from jinja2 import Template
from PyPDF2 import PdfMerger
from weasyprint import CSS, HTML

from script.src.config import Config
from script.src.constants import MEDIA_TYPES, Extensions, Files
from script.src.utils import (
    get_media_path,
    get_project_content,
    get_project_metadata,
    get_project_path,
    load_template,
    setup_logging,
    strip_emoji,
)


class PDFHandler:
    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logging(__name__)
                
        # Initialize Markdown converter
        self.md = markdown.Markdown(extensions=['extra', 'codehilite'])

    def publish(self) -> None:
        # Search recursively for temp_pdf folders
        temp_pdf_folders = list(Path(self.config.base_dir).rglob('temp_pdf'))
        output_folder = Path(self.config.base_dir / 'output_pdf')
        
        try:
            # Create output folder if it doesn't exist
            output_folder.mkdir(exist_ok=True)
            
            for temp_folder in temp_pdf_folders:
                # Move PDFs
                for pdf_file in temp_folder.glob('*.pdf'):
                    shutil.move(str(pdf_file), str(output_folder / pdf_file.name))
                
                # Move images
                for extension in Extensions.IMAGE:
                    for image_file in temp_folder.glob(extension):
                        shutil.move(str(image_file), str(output_folder / image_file.name))
                
                # Delete temp folder and its contents
                shutil.rmtree(temp_folder)
                self.logger.info(f"Processed and removed {temp_folder}")

            # Combine PDFs
            pdf_files = list(output_folder.glob('*.pdf'))
            if pdf_files:
                merger = PdfMerger()
                
                # Add each PDF to the merger
                for pdf in pdf_files:
                    merger.append(str(pdf))
                
                # Write combined PDF
                combined_path = output_folder / 'combined.pdf'
                merger.write(str(combined_path))
                merger.close()
                
                # Delete source PDFs
                for pdf in pdf_files:
                    pdf.unlink()
                
                self.logger.info(f"Combined PDFs created at {combined_path}")
                    
        except Exception as e:
            self.logger.error(f"Error processing temp folders: {e}")
            raise


    def stage_pdf(self, name: str, collate_images: bool) -> None:
        """Generate a PDF for a project"""

        project_dir = get_project_path(self, name)
        metadata = get_project_metadata(self, name)
        project = metadata['project']

        self.logger.info(f"Generating PDF for {name}")

        try:
            
            temp_dir = Path(project_dir / 'temp_pdf')
            temp_dir.mkdir(exist_ok=True)

            # Read content file
            content = get_project_content(self, name)
            # Convert markdown to HTML
            html_content = self.md.convert(content)

            specs = metadata['physical_specifications']
            
            dimensions = f"{specs['dimensions']['width']}{specs['dimensions']['unit']} w x {specs['dimensions']['height']}{specs['dimensions']['unit']} h x {specs['dimensions']['depth']}{specs['dimensions']['unit']} d"
            weight = f"{specs['weight']['value']} {specs['weight']['unit']}"
            materials = ", ".join(specs['materials'])

            reqs = metadata['technical_requirements']

            lighting = reqs['lighting']
            mounting = reqs['mounting']
            temperature_range = reqs['environmental']['temperature_range']
            humidity_range = reqs['environmental']['humidity_range']
            ventilation_needs = reqs['environmental']['ventilation_needs']

            ex = metadata['exhibition']

            setup_instructions = ex['setup']['instructions']
            setup_time = ex['setup']['time_required']
            setup_people = ex['setup']['people_required']
            setup_tools = ", ".join(ex['setup']['tools_required'])

            maintenance_supplies = ", ".join(ex['maintenance']['supplies_needed'])
            maintenance_instructions = ex['maintenance']['tasks']

            # Prepare template data
            template_data = {
                'title': strip_emoji(project['display_name']).strip(),
                'description': project.get('description', ''),
                'date': project['date_created'],
                'website': f"{self.config.website_domain}/{name}",
                'dimensions': dimensions,
                'weight': weight,
                'materials': materials,
                'lighting': lighting,
                'mounting': mounting,
                'temperature_range': temperature_range,
                'humidity_range': humidity_range,
                'ventilation_needs': ventilation_needs,
                'setup_instructions': setup_instructions,
                'setup_time': setup_time,
                'setup_tools': setup_tools,
                'setup_people': setup_people,
                'maintenance_supplies': maintenance_supplies,
                'maintenance_instructions': maintenance_instructions,
                'content': html_content,
            }

            css = CSS(string=load_template(self, Files.PDF_STYLE))

            # Get list of images and create PDFs for each
            images = []
            for extension in Extensions.IMAGE:
                images.extend(temp_dir.glob(extension))

            image_pdfs = []
            if collate_images:
                
                image_groups = [images[i:i + 2] for i in range(0, len(images), 2)]

                for group in image_groups:
                    image_template_data = {
                        'title': strip_emoji(project['display_name']).strip(),
                        'images': [f"{image.absolute()}" for image in group]
                    }
                    template = Template(load_template(self, Files.PDF_IMAGE_LAYOUT))
                    rendered_html = template.render(**image_template_data)
                    image_pdf = HTML(string=rendered_html, base_url=str(temp_dir)).render(stylesheets=[css])
                    image_pdfs.extend(image_pdf.pages)

                    [Path(image).unlink() for image in group]
            else:
                template_data['image_file_names'] = ", ".join(f.name for f in images)

            # Generate main content PDF
            template = Template(load_template(self, Files.PDF_LAYOUT))
            html_string = template.render(**template_data)
            main_pdf = HTML(string=html_string).render(stylesheets=[css])

            # Combine main content with image pages
            all_pages = main_pdf.pages + image_pdfs
            output_pdf = main_pdf.copy(all_pages)
            output_path = temp_dir / f"{name}.pdf"
            output_pdf.write_pdf(output_path)

            self.logger.info(f"Successfully generated PDF for {name}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate PDF for {name}: {e}")
            raise

    def stage_media(self, name: str, filename_prepend: str='') -> None:
        """Rename media files in-place with sequential naming."""
        project_dir = get_project_path(self, name)

        self.logger.info(f"Organizing media for {name}")

        try:
            temp_dir = project_dir / 'temp_pdf'
            temp_dir.mkdir(exist_ok=True)

            for media_type in MEDIA_TYPES:
                type_dir = get_media_path(self, project_dir, media_type)
                if not type_dir.exists():
                    continue

                counter = 1
                files = []
                
                # Get all files of supported types
                if media_type == 'images':
                    for ext in Extensions.IMAGE:
                        files.extend(type_dir.glob(f'*{ext}'))
                elif media_type == 'videos':
                    for ext in Extensions.VIDEO:
                        files.extend(type_dir.glob(f'*{ext}'))
                
                # Rename files in place
                for file in sorted(files):
                    new_name = f"{filename_prepend}_{name}_{counter}{file.suffix}"
                    shutil.copy(str(file), str(temp_dir / new_name))
                    counter += 1
        except Exception as e:
            self.logger.error(f"Failed to stage media for PDF for {name}: {e}")
            raise