from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    base_dir: Path
    website_domain: str
    github_username: str
    github_token: str
    jekyll_dir: Path
    enable_things3: bool