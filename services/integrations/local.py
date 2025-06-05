from pathlib import Path

from entities.integration.implementations.local import LocalIntegration
from entities.integration.service import IntegrationService


class LocalIntegrationService(IntegrationService):
    """Service specifically for local implementations"""
    
    @property
    def entity_class(self):
        return LocalIntegration
    
    def create_local_integration(self, name: str, base_dir: str = None, use_git: bool = True) -> LocalIntegration:
        """Create a new local integration"""
        if base_dir and not Path(base_dir).exists():
            raise ValueError(f"Base directory does not exist: {base_dir}")
        
        return self.create_integration(
            integration_class=LocalIntegration,
            name=name,
            base_dir=base_dir or str(Path.home()),
            use_git=use_git
        )
    
    def get_project_files(self, integration: LocalIntegration, project) -> dict:
        """Get information about project files"""
        project_path = integration.path(project)
        
        if not project_path.exists():
            return {"exists": False, "path": str(project_path)}
        
        files = {
            "exists": True,
            "path": str(project_path),
            "content_files": [],
            "media_files": [],
            "src_files": []
        }
        
        # Check content files
        content_dir = project_path / 'content'
        if content_dir.exists():
            files["content_files"] = [f.name for f in content_dir.glob('*') if f.is_file()]
        
        # Check media files
        media_dir = project_path / 'media'
        if media_dir.exists():
            files["media_files"] = [f.name for f in media_dir.glob('**/*') if f.is_file()]
        
        # Check src files
        src_dir = project_path / 'src'
        if src_dir.exists():
            files["src_files"] = [f.name for f in src_dir.glob('**/*') if f.is_file()]
        
        return files