# 🦋 Luna

Luna is a tool for artists and creative technologists which automates the creation, management, and syndication of art and personal projects across various channels. It streamlines the process of maintaining consistent organization of your work across different platforms.

## Overview

Luna simplifies your creative workflow through a command-line interface that:

- Creates standardized local project directories for work-in-progress files and media
- Sets up GitHub repositories with proper structure and documentation
- Generates consistent metadata across all your projects
- Optionally integrates with Things 3 for task management (macOS only)

When you're ready to share your work, Luna facilitates publication through various channels:

- Portfolio website (designed for Jekyll-based sites)
- GitHub repositories
- PDF generation for exhibition submissions and open calls
- Raw file exports for other purposes

## Features

- **Single Source of Truth**: Maintain all project information in one place to eliminate redundancy
- **Standardized Structure**: Consistent project organization for easier navigation and management
- **Multi-Channel Publishing**:
  - **Website**: Generate Jekyll-compatible posts and media files
  - **GitHub**: Create repositories and update README files
  - **PDF**: Format project documentation for submissions with customizable options
  - **Raw**: Export organized files for other platforms
- **Optional Integrations**:
  - Things 3 on macOS for task management

## Installation

1. Clone the repository:
```bash
git clone git@github.com:yourusername/luna.git
cd luna
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r src/requirements.txt
```

4. Create your environment file:
```bash
cp src/.env.example .env
# Edit .env with your values
```

5. Set up your personal info:
```bash
cp src/personal-info.yml.example src/personal-info.yml
# Edit with your information
```

## Configuration

Edit the `personal-info.yml` file with your information, it will be used across various channels where personalization is needed.

Edit the `.env` file with your specific configuration settings:

### Required Settings
- `PROJECT_BASE_DIR`: Path where you want to create and manage projects
- `WEBSITE_DOMAIN`: The domain where your Jekyll website is hosted
- `WEBSITE_DIR`: Path to your website directory
- `WEBSITE_POSTS`: Relative path to posts directory (e.g., "_posts")
- `WEBSITE_MEDIA`: Relative path to media directory (e.g., "_media")
- `WEBSITE_PAGES`: Relative path to pages directory (e.g., "_pages")
### Optional Settings
- `GITHUB_USERNAME` and `GITHUB_TOKEN`: For GitHub integration
- `ENABLE_THINGS3`: Set to "true" to enable Things 3 integration
- `THINGS3_AREA`: Area in Things 3 where projects should be created

## Usage

All commands are run using the main script:

### Creating a New Project

```bash
python -m src.script.main create
```

This interactive command will:
1. Prompt for a project display name
2. Create a standardized directory structure
3. Initialize basic metadata files
4. Optionally create a GitHub repository
5. Optionally create a Things 3 project (if enabled)

### Listing Projects

```bash
python -m src.script.main list

# Sort by different criteria
python -m src.script.main list --sort-by date
python -m src.script.main list --sort-by priority
python -m src.script.main list --sort-by status

# Filter by status
python -m src.script.main list --status in_progress
```

### Renaming a Project

```bash
python -m src.script.main rename
```

This updates the project locally and across all integration channels.

### Deleting a Project

```bash
python -m src.script.main delete
# or
python -m src.script.main delete --projects project-name
```

### Publishing to Channels

```bash
# Publish specific projects to all channels
python -m src.script.main publish --projects project1 project2 --all-channels

# Publish all projects to specific channels
python -m src.script.main publish --all-projects --channels github web

# Publish specific projects to specific channels
python -m src.script.main publish --projects project1 --channels pdf
```

### Channel-Specific Options

#### PDF Channel

Supports generating a PDF with media in the PDF, or with media as files separate to the PDF.

```bash
# Generate PDF with images collated in the same document
python -m src.script.main publish --projects project1 --channels pdf --collate-images

# Specify submission name for PDF
python -m src.script.main publish --projects project1 --channels pdf --submission-name "Gallery-Open-Call-2023"



# Generate PDF with separate image files and specific dimensions
python -m src.script.main publish --projects project1 --channels pdf --max-width 1200 --max-height 800

# Add a prefix to exported filenames
python -m src.script.main publish --projects project1 --channels pdf --filename-prepend "Exhibition-2023-"
```

#### GitHub Channel

```bash
# Stage (generate README.md without pushing)
python -m src.script.main stage --projects project1 --channels github

# Publish with commit message
python -m src.script.main publish --projects project1 --channels github --commit-message "Updated project documentation"
```

#### Website Channel

```bash
# Stage website content
python -m src.script.main stage --projects project1 --channels web

# Publish to website: will create a post for the project with front matter containing metadata and file path references for media files
python -m src.script.main publish --projects project1 --channels web
```

#### Raw Channel

```bash
# Export files to _output folder
python -m src.script.main publish --projects project1 --channels raw
```

## Project Structure

Each project is created with the following structure:

```
project-name/
├── src/                  # Source code for the project
├── media/                # Media files for publication
│   ├── images/           # Image files
│   ├── videos/           # Video files
│   ├── audio/            # Audio files
│   ├── models/           # 3D model files
│   ├── docs/             # Document files
│   └── embeds/           # Embed content
├── media-internal/       # Working/draft media files (not published)
│   ├── images/
│   ├── videos/
│   ├── audio/
│   ├── models/
│   └── docs/
├── content/              # Project content and metadata
│   ├── content.md        # Main content markdown
│   ├── metadata.yml      # Project metadata
│   └── README.md         # Project README
```

The `media-internal` directory is intended for work-in-progress assets that won't be used in channel publication. When files are ready for publication, move them to the corresponding subdirectory in the `media` folder and they will be automatically used.

## Development

### Project Structure

```
luna/
├── src/                  # Source code
│   ├── script/           # Main script modules
│   │   ├── channels/     # Publication channel handlers
│   │   ├── templates/    # Templates for various outputs
│   │   └── utils.py      # Utility functions
│   ├── requirements.txt  # Project dependencies
│   └── .env.example      # Environment variable template
└── tests/                # Test suite (see testing strategy)
```

### Adding a New Channel

1. Create a new handler file in the `src/script/channels/` directory
2. Create any necessary templates in the `src/script/templates/` directory
3. Add your channel to the channel registry in `src/script/main.py`
4. Implement the required channel interface methods (stage, publish, etc.)

## Testing

See the [Testing Strategy](./tests/README.md) document for details on how to run and create tests for Luna.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.