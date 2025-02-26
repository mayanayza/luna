from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    base_dir: Path
    website_domain: str
    github_username: str
    github_token: str
    instagram_username: str
    instagram_password: str
    website_dir: Path
    enable_things3: bool
    website_posts: str
    website_media: str
    website_pages: str
    things3_area: str

    @property
    def github_url_path(self) -> str:
        return f"https://github.com/{self.github_username}"

    @property
    def website_posts_dir(self) -> Path:
        return self.website_dir / self.website_posts

    @property
    def website_media_dir(self) -> Path:
        return self.website_dir / self.website_media

    @property
    def website_pages_dir(self) -> Path:
        return self.website_dir / self.website_pages