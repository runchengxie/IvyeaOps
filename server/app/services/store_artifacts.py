"""Source-labelled local store snapshots and immutable audit reports.

This module never contacts a marketplace or invokes a model. Importing a
snapshot means recording supplied evidence, not verifying its accuracy.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

_ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}\Z")


def validate_id(value: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError('Use a store/report ID of 1–80 letters, digits, underscores or hyphens')
    return value


class StoreSnapshot(BaseModel):
    model_config = ConfigDict(extra='forbid')
    store_id: str
    platform: str = Field(min_length=1, max_length=40)
    marketplace: str = Field(min_length=1, max_length=40)
    captured_at: datetime
    source: str = Field(min_length=1, max_length=500)
    coverage: list[str] = Field(min_length=1, max_length=100)
    limitations: list[str] = Field(max_length=100)
    data: dict[str, Any]

    @field_validator('store_id')
    @classmethod
    def valid_store(cls, value):
        return validate_id(value)

    @field_validator('platform', 'marketplace', 'source')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Must not be blank')
        return value.strip()

    @field_validator('captured_at')
    @classmethod
    def aware(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('captured_at requires an explicit timezone')
        return value


def _root() -> Path:
    from app.core.config import settings
    return Path(settings.data_dir) / 'store-artifacts'


def _write_new(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, allow_nan=False, indent=2)
    if len(text.encode('utf-8')) > 2_000_000:
        raise ValueError('Artifact exceeds 2 MB')
    temporary = path.with_suffix('.' + secrets.token_hex(16) + '.tmp')
    try:
        with temporary.open('x', encoding='utf-8') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def snapshot_guard():
    root = _root()
    root.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(root / 'publication-lock.sqlite3', timeout=30)
    try:
        conn.execute('BEGIN IMMEDIATE')
        yield
        conn.commit()
    finally:
        conn.close()


def import_snapshot(payload: dict) -> dict:
    snapshot = StoreSnapshot.model_validate(payload).model_dump(mode='json')
    # Append snapshots rather than overwrite evidence used by older reports.
    directory = _root() / 'snapshots' / snapshot['store_id']
    with snapshot_guard():
        snapshot_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '_' + secrets.token_hex(4)
        snapshot['snapshot_id'] = snapshot_id
        _write_new(directory / f'{snapshot_id}.json', snapshot)
    return snapshot


def read_snapshot(store_id: str, snapshot_id: str | None = None) -> dict:
    directory = _root() / 'snapshots' / validate_id(store_id)
    files = [directory / f'{validate_id(snapshot_id)}.json'] if snapshot_id is not None else sorted(directory.glob('*.json'), reverse=True)
    if not files:
        raise FileNotFoundError(f'No imported snapshot for {store_id}; collect or import evidence first')
    payload = json.loads(files[0].read_text('utf-8'))
    stored_id = payload.pop('snapshot_id', files[0].stem)
    if stored_id != files[0].stem:
        raise ValueError('Snapshot ID does not match its stored version')
    snapshot = StoreSnapshot.model_validate(payload).model_dump(mode='json')
    if snapshot['store_id'] != store_id:
        raise ValueError('Snapshot store does not match requested store')
    return {**snapshot, 'snapshot_id': stored_id}


def save_report(store_id: str, snapshot_id: str, title: str, markdown: str) -> dict:
    validate_id(snapshot_id)
    if not isinstance(title, str) or not title.strip() or len(title) > 200:
        raise ValueError('Report title must contain 1–200 characters')
    if not isinstance(markdown, str) or not markdown.strip() or len(markdown) > 200_000:
        raise ValueError('Report markdown must contain 1–200000 characters')
    snapshot = read_snapshot(store_id, snapshot_id)
    report = {'report_id': secrets.token_hex(16), 'store_id': store_id,
              'created_at': datetime.now(timezone.utc).isoformat(),
              'title': title.strip(), 'markdown': markdown,
              'snapshot_id': snapshot['snapshot_id'],
              'snapshot_captured_at': snapshot['captured_at'], 'snapshot': snapshot}
    _write_new(_root() / 'reports' / f"{report['report_id']}.json", report)
    return report


def read_report(report_id: str) -> dict:
    return json.loads((_root() / 'reports' / f'{validate_id(report_id)}.json').read_text('utf-8'))
