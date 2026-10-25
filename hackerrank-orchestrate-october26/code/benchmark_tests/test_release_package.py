"""Release packaging boundaries using independent synthetic files."""
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import package


def project(tmp_path, monkeypatch):
    monkeypatch.setattr(package, 'ROOT', tmp_path)
    (tmp_path / 'code').mkdir()
    (tmp_path / 'code/main.py').write_text('print("synthetic")\n', encoding='utf-8')
    (tmp_path / 'README.md').write_text('Project notes', encoding='utf-8')
    (tmp_path / 'SUBMISSION_README.md').write_text('Release setup', encoding='utf-8')
    (tmp_path / 'requirements.txt').write_text('', encoding='utf-8')


def test_release_is_deterministic_and_excludes_non_source_material(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    (tmp_path / 'code/explore').mkdir()
    (tmp_path / 'code/explore/scratch.py').write_text('scratch', encoding='utf-8')
    (tmp_path / 'code/.env').write_text('synthetic environment', encoding='utf-8')
    (tmp_path / 'dataset').mkdir()
    (tmp_path / 'dataset/private.csv').write_text('synthetic input', encoding='utf-8')
    (tmp_path / 'output.csv').write_text('synthetic prediction', encoding='utf-8')
    (tmp_path / 'log.txt').write_text('synthetic transcript', encoding='utf-8')
    first = tmp_path / 'release/code.zip'
    package.build(first)
    second = tmp_path / 'second.zip'
    package.build(second)
    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as archive:
        assert archive.testzip() is None
        assert archive.read('README.md') == b'Release setup'
        assert set(archive.namelist()) == {'README.md', 'requirements.txt', 'code/main.py'}


def test_embedded_archive_is_rejected(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    (tmp_path / 'code/nested.zip').write_bytes(b'synthetic archive')
    with pytest.raises(SystemExit, match='forbidden'):
        package.build(tmp_path / 'release.zip')


def test_secret_bearing_source_is_rejected(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    (tmp_path / 'code/credential.py').write_bytes(b'sk-' + b'X' * 24)
    with pytest.raises(SystemExit, match='secret-bearing'):
        package.build(tmp_path / 'release.zip')


def test_interrupted_zip_write_preserves_the_previous_release(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    target = tmp_path / 'release.zip'
    target.write_bytes(b'previous complete release')
    def fail(*args, **kwargs): raise OSError('synthetic interrupted write')
    monkeypatch.setattr(zipfile.ZipFile, 'writestr', fail)
    with pytest.raises(OSError): package.build(target)
    assert target.read_bytes() == b'previous complete release'
    assert not list(tmp_path.glob('.package-*'))
