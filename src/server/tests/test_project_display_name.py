import pytest
from app.agents.routers.projects import _display_name


@pytest.mark.parametrize('path', ['/work/project', '/work/project/', r'C:\work\project',
                                  'C:\\work\\project\\', r'\\server\share\project'])
def test_project_basename_is_portable(path):
    assert _display_name({'project_path': path, 'custom_project_name': None}) == 'project'


def test_custom_project_name_wins():
    assert _display_name({'project_path': r'C:\work\project', 'custom_project_name': 'Custom'}) == 'Custom'
