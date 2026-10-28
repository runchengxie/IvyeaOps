from types import SimpleNamespace


def test_windows_sync_uses_files_without_launching_cli(monkeypatch):
    from app.agents import synchronizer
    monkeypatch.setattr(synchronizer, 'os', SimpleNamespace(name='nt'))
    monkeypatch.setattr(synchronizer, '_synchronize_hermes_from_files', lambda: 7)
    def unexpected_cli():
        raise AssertionError('Windows project listing must not launch Hermes CLI')
    monkeypatch.setattr(synchronizer, '_hermes_bin', unexpected_cli)
    assert synchronizer.synchronize_hermes() == 7
