import shutil
from pathlib import Path

# import markdown
from PyPDF2 import PdfMerger
from weasyprint import HTML

from script.src.channels._channel import Channel
from script.src.config import Config
from script.src.constants import Media
from script.src.utils import (
    get_media_files,
    get_project_metadata,
    get_project_path,
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

        self.media = {
           Media.IMAGES.TYPE: Media.IMAGES.EXT
        }

    def publish(self) -> None:
        # Search recursively for temp_pdf folders
        temp_pdf_folders = list(Path(self.config.base_dir).rglob('temp_pdf'))
        output_folder = Path(self.config.base_dir / '_output')
        
        try:
            # Create output folder if it doesn't exist
            output_folder.mkdir(exist_ok=True)
            
            for temp_folder in temp_pdf_folders:
                # Move PDFs
                for pdf_file in temp_folder.glob('*.pdf'):
                    shutil.move(str(pdf_file), str(output_folder / pdf_file.name))
                
                # Move images
                for extension in self.media[Media.IMAGES.TYPE]:
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
                
                self.logger.info(f"Published PDF at {combined_path}")
        except Exception as e:
            self.logger.error(f"Error publishing PDF: {e}")
            raise

    def stage(self, name, collate_images, max_width, max_height, filename_prepend) -> None:
        self.generate_pdf(name, max_width, max_height,filename_prepend, collate_images)

    def generate_pdf(self, name, max_width, max_height, filename_prepend, collate_images):
        """Generate PDF with optional image collation."""

        try:
            project_dir = get_project_path(self, name)
            metadata = get_project_metadata(self, name)
            temp_dir = project_dir / 'temp_pdf'
            Path(temp_dir).mkdir(exist_ok=True)

            image_pdfs = []
            context = {}
            images = get_media_files(self, name, Media.IMAGES.TYPE)
            if collate_images:
                image_pdfs = self.generate_images_pdf(name, images)
            else:
                context['image_file_names'] = self.stage_images(name, images, max_width, max_height, filename_prepend)

            if metadata['project']['featured_content']['type'] == 'image':
                context['featured_image'] = str((project_dir / 'media' / Media.IMAGES.TYPE / metadata['project']['featured_content']['source']).absolute())
            
            # Generate main content PDF
            html_string = self.tp.process_template(name, 'pdf/project_cover.html', context)
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

    def generate_images_pdf(self, name, images):
        try:
            project_dir = get_project_path(self, name)

            image_groups = [images[i:i + 2] for i in range(0, len(images), 2)]
            image_pdfs = []

            for group in image_groups:
                context = {
                    'images': [image.resolve() for image in group]
                }
                html_string = self.tp.process_template(name, 'pdf/project_images.html', context)
                image_pdf = HTML(string=html_string, base_url=project_dir).render()
                image_pdfs.extend(image_pdf.pages)

            self.logger.info(f"Generated image PDFs for {name}")
            return image_pdfs
        except Exception as e:
            self.logger.error(f"Failed to generate image PDF for {name}: {e}")
            raise
            
    def stage_images(self, name, images, max_width, max_height, filename_prepend):
        try:
            project_dir = get_project_path(self, name)
            temp_dir = project_dir / 'temp_pdf'
            Path(temp_dir).mkdir(exist_ok=True)
            
            counter = 1
            new_names = []
            
            for file in sorted(images):
                file = resize_image_file(file, max_width, max_height)
                new_name = f"{name}_{counter}{file.suffix}"
                if filename_prepend:
                    new_name = f"{filename_prepend}_{new_name}"
                new_names.append(new_name)
                shutil.copy(str(file), str(temp_dir / new_name))
                counter += 1
            self.logger.info(f"Staged images for {name}")
            return ", ".join(new_names)
        except Exception as e:
            self.logger.error(f"Failed stage images for {name}: {e}")
            raise