import pytest
import tempfile
from common.enums import EntityType
from application.context import ApplicationContext

def test_simple():
    """Simple test to verify pytest is working"""
    assert 1 + 1 == 2

@pytest.fixture
def temp_app():
    """Simple isolated app for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        import os
        os.environ['DB_DIR'] = temp_dir
        os.environ['DB_NAME'] = 'test'

        app = ApplicationContext()
        app.initialize()
        yield app


class TestProjectWorkflow:
    """Test the main user workflows"""

    def test_create_list_delete_project(self, temp_app):
        """Test complete project lifecycle"""
        project_service = temp_app.get_registry(EntityType.PROJECT).service

        # Create
        project = project_service.create(name="test-project", emoji="🚀")
        assert project.name == "test-project"

        # List
        projects = project_service.list_entities()
        assert len(projects) == 1
        assert projects[0].name == "test-project"

        # Delete
        result = project_service.delete(project)
        assert result is True

        # Verify deletion
        projects = project_service.list_entities()
        assert len(projects) == 0


class TestIntegrationWorkflow:
    """Test integration management"""

    def test_project_integration_lifecycle(self, temp_app):
        """Test adding/removing implementations from projects"""
        project_service = temp_app.get_service(EntityType.PROJECT)
        integration_service = temp_app.get_service(EntityType.INTEGRATION)

        # Create entities
        project = project_service.create(name="test-project")
        integration = integration_service.create(name="local-int", submodule="local")

        # Add integration to project
        pi = project_service.add_integration(project, integration)
        assert pi is not None

        # Verify integration is listed
        integrations = project_service.get_integrations(project)
        assert len(integrations) == 1


# tests/test_validation.py - Test edge cases
class TestValidation:
    """Test validation and error handling"""

    def test_invalid_names_rejected(self, temp_app):
        """Test that invalid names are properly rejected"""
        project_service = temp_app.get_registry(EntityType.PROJECT).service

        with pytest.raises(ValueError):
            project_service.create(name="")  # Empty name

        with pytest.raises(ValueError):
            project_service.create(name="   ")  # Whitespace only