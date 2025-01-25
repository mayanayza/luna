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

    @property
    def github_url_path(self) -> str:
        return f"https://github.com/{self.github_username}"

    @property
    def website_posts_dir(self) -> Path:
        return self.jekyll_dir / '_posts'

    @property
    def website_media_dir(self) -> Path:
        return self.jekyll_dir / 'media'

    @property
    def website_pages_dir(self) -> Path:
        return self.jekyll_dir / '_pages'