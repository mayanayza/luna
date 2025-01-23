# Project Automation
A tool for automating the creation and management of project documentation. Creates local project directories, GitHub repositories, Jekyll site entries, and Things 3 projects with consistent organization and metadata.

## Setup
1. Clone the repository:
```bash
git clone git@github.com:yourusername/project-automation.git
cd project-automation
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create your environment file:
```bash
cp .env.example .env
# Edit .env with your values
```

## Environment Variables
- `PROJECT_BASE_DIR`: Base directory for all projects (default: ~/Documents/Projects)
- `JEKYLL_SITE_PATH`: Path to Jekyll site (default: ~/portfolio-site)
- `GITHUB_USERNAME`: Your GitHub username
- `GITHUB_TOKEN`: Your GitHub personal access token
- `ENABLE_THINGS3`: Enable/disable Things 3 integration (true/false)

## Usage

### Create a new project:
```bash
python src/script.py --command create
```

### List all projects:
```bash
python src/script.py --command list
```
This will show all projects with their display names, canonical names, creation dates, and status.

### Sync project updates:
```bash
# Sync all out-of-date projects
python src/script.py --command sync

# Sync specific project
python src/script.py --command sync --name plant-autowater
```

### Rename a project:
```bash
# Start rename process (will prompt for new name)
python src/script.py --command rename --name plant-autowater
```
The rename command will:
- Update the Things 3 project name
- Rename the local directory
- Update all project metadata
- Update README headers
- Rename the GitHub repository
- Update Jekyll site files

## Project Structure
Each project is created with the following structure:
```
project-name/
├── src/              # Source code
├── docs/             # Documentation
├── hardware/         # Hardware-related files
├── media/           # Published media (tracked in git)
│   ├── images/
│   ├── videos/
│   └── models/
├── media-internal/  # Internal media (git-ignored)
│   ├── images/
│   ├── videos/
│   └── models/
├── README.md        # Project documentation
└── metadata.yml     # Project metadata
```

## Repository Structure
```
project-automation/
├── src/
│   └── script.py
├── templates/
│   ├── readme.md           # Template for project READMEs
│   ├── metadata.yml        # Template for project metadata
│   ├── gitignore          # Template for project .gitignore
│   └── project-page.md     # Template for Jekyll project pages
├── .env.example            # Example environment variables
├── .env                    # Local environment variables (git-ignored)
├── .gitignore             # Git ignore for this repo
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Features
- Creates standardized project structure
- Initializes git repository and pushes to GitHub
- Creates Things 3 project in specified area
- Manages both published and internal media
- Syncs project metadata with Jekyll portfolio site
- Lists all projects with their details
- Handles emoji in project names
- Interactive rename functionality:
  - Updates Things 3 project names
  - Renames GitHub repositories
  - Updates Jekyll site files
  - Maintains project history
- Automatic metadata tracking and synchronization
- Clear separation of display names and canonical names

## Development
To modify templates or add features:
1. Templates are in the `templates/` directory
2. Main script is in `src/script.py`
3. Add any new dependencies to `requirements.txt`

## Things 3 Integration
The script integrates with Things 3 on macOS:
- Creates projects in a specified area (configured as "🎨 Art")
- Updates project names when using the rename command
- Manages project organization automatically

## Naming Convention
Projects use two types of names:
- Display Name: User-friendly name with emoji (e.g., "🌱 Plant Autowater")
- Canonical Name: URL-safe, lowercase name (e.g., "plant-autowater")

The script automatically handles conversion between these formats.