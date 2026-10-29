"""The published documentation build must contain only public, usable pages."""
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[3]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.hrefs.extend(value for name, value in attrs if name == 'href' and value)


def test_site_build_has_localized_pages_and_resolves_local_links(tmp_path):
    destination = tmp_path / 'site'
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/build-docs-site.py'), '--output', str(destination)],
                            cwd=tmp_path, capture_output=True, encoding='utf-8', timeout=45)
    assert result.returncode == 0, result.stderr
    assert (destination / 'index.html').is_file()
    assert 'eMAG' in (destination / 'en/index.html').read_text('utf-8')
    assert 'eMAG' in (destination / 'zh-CN/index.html').read_text('utf-8')
    assert (destination / 'assets/emag-workbench.png').is_file()
    assert 'synthetic' in (destination / 'en/index.html').read_text('utf-8').lower()
    assert '模拟' in (destination / 'zh-CN/index.html').read_text('utf-8')
    assert not (destination / 'data').exists()
    for page in destination.rglob('*.html'):
        parser = Links()
        parser.feed(page.read_text('utf-8'))
        for href in parser.hrefs:
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            assert not parsed.path.startswith('/'), (page, href)
            target = (page.parent / unquote(parsed.path)).resolve()
            assert target.is_file(), (page, href)


def test_site_build_preserves_existing_output(tmp_path):
    destination = tmp_path / 'site'
    destination.mkdir()
    marker = destination / 'existing.txt'
    marker.write_text('keep', encoding='utf-8')
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/build-docs-site.py'), '--output', str(destination)],
                            capture_output=True, encoding='utf-8', timeout=45)
    assert result.returncode != 0
    assert marker.read_text(encoding='utf-8') == 'keep'
