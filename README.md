# 🦋 Luna

Luna is a tool for artists and creative technologists which automates the creation, management, and syndication of art and personal projects across various channels. As I started to create more art, the toil of managing and organizing my work across different platforms became annoying, so I decided to create a tool to streamline it all.

Luna does the following through a simple CLI:
- Creates local project directories to store work-in-progress files and media, 
- Sets up a GitHub repository for your project
- Optionally, creates a Things 3 project
...all with consistent organization and metadata.

Once ready, Luna also facilitates syndication of project content through various channels:
- A portfolio website (designed for websites powered by Jekyll)
- Github
- PDF summaries for submission to open call and exhibitions

Almost all of the content on my website is managed using Luna.

## Setup
1. Clone the repository:
```bash
git clone git@github.com:yourusername/project-automation.git
cd script
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip3 install -r requirements.txt
```

4. Create your environment file:
```bash
cp .env.example .env
# Edit .env with your values
```

5. Run script commands from root directory
```bash
cd ..
```

## Environment Variables
- `WEBSITE_DOMAIN`: The domain on which your Jekyll website will ultimately be served
- `PROJECT_BASE_DIR`: Path for where you would like to create and manage projects
- `WEBSITE_DIR`: Path to where your website content is located
- `WEBSITE_POSTS`: Relative path to WEBSITE_DIR where your website posts are located
- `WEBSITE_MEDIA`: Relative path to WEBSITE_DIR where your website media is located
- `WEBSITE_PAGES`: Relative path to WEBSITE_DIR where your website pages are located
- `ENABLE_ROADMAP`: Enable/disable generating a roadmap page based on your projects for your website
- `GITHUB_USERNAME`: Your GitHub username
- `GITHUB_TOKEN`: Your GitHub personal access token
- `ENABLE_THINGS3`: Enable/disable Things 3 integration (true/false)
- `THINGS3_AREA`: Area where projects should be created

## Usage

### Create a new project:
```bash
python -m script.src.main --command create
python -m script.src.main --c create
```

### List all projects:
```bash
python -m script.src.main --command list
python -m script.src.main --c list
```
This will show all projects with their names, creation dates, and status.

### Rename project:
```bash
python -m script.src.main --command rename
python -m script.src.main --c rename
```

### Delete project:
```bash
python -m script.src.main --command delete
python -m script.src.main --c delete
```

### Publish project updates:
```bash
# Publish all projects to all channels
python -m script.src.main --command publish --all-projects --all-channels

# Publish specific projects to all channels
python -m script.src.main --command publish --projects project1 project2 --all-channels
python -m script.src.main --command publish --p project1 project2 --all-channels

# Publish specific projects to specific channels
python -m script.src.main --command publish --p project1 project2 --channels channel1 channel2
python -m script.src.main --command publish --p project1 project2 --ch channel1 channel2
```

### Available channels:
```bash
web
pdf
raw
github
```

### Channel-specific publishing options

#### PDF
```bash
# Generate PDF with images collated into same document (only if not using --filename-prepend). **Optional, default is false.**
python -m script.src.main --c publish --p project1 --ch pdf --collate-images
python -m script.src.main --c publish --p project1 --ch pdf -ci

# Generate PDF with a filename prepended to generated image files (only if not using --collate-images). **Optional, default is ''**
python -m script.src.main --c publish --p project1 --ch pdf --filename-prepend
python -m script.src.main --c publish --p project1 --ch pdf -fp
```

#### Github
```bash
# Commit message when publishing to Github. **Required**
python -m script.src.main --c publish --p project1 --ch github --commit-message 'message'
python -m script.src.main --c publish --p project1 --ch github -cm 'message'
```

## Project Structure
Each project is created with the following structure:
```
project-name/
├── src/
├── media/
│   ├── images/
│   ├── videos/
│   ├── audio/
│   ├── docs/
│   └── models/
├── media-internal/
│   ├── images/
│   ├── videos/
│   ├── audio/
│   ├── docs/
│   └── models/
├── content/ 
│   ├── content.md
│   └── README.md
└── metadata.yml
```

media-internal is for organizing WIP assets which wil not be committed to Github. Final media files which are ready to be syndicated in different channels, media files should be moved to the corresponding media/ subfolder.

The script combines assets from the media/ and content/ folders to generate the output for different channels as follows:

- Github: Combines README.md + content.md into a final README.md which is generated in the project-name/folder
- PDF: Combines content.md and metadata.yml into a PDF summary of the project. If multiple projects are chosen, will merge all project PDF summaries into a single file.
- Website: Combines content.md, metadata.yml into website post content. Also optionally generates a roadmap page based on project status.
- Raw: Outputs all publication files (media + content folders).

## Features
- Provides a single source-of-truth for all project information to eliminate toil in managing across various channels
- Creates standardized project structure on local machine
- Initializes git repository
- Provides structure for managing media files
- Syndicates content across various channels

## Development
To add a channel
1. Create a new .py file for the channel in the channels/ directory
2. Create any necessary template files for the channel in the templates/ directory
3. Add automation to automation.py
4. Add channel to channel registry in main.py

## Things 3 Integration
The script provides a simple integration with Things 3 on macOS, and will create a project in the area specified in the .env file upon project creation.

## Media







