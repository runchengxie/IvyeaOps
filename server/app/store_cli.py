"""Local evidence import: python -m app.store_cli import-snapshot FILE."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services import store_artifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    importer = commands.add_parser('import-snapshot')
    importer.add_argument('file', type=Path)
    reader = commands.add_parser('read-snapshot')
    reader.add_argument('store_id')
    report = commands.add_parser('read-report')
    report.add_argument('report_id')
    args = parser.parse_args()
    try:
        if args.command == 'import-snapshot':
            if args.file.stat().st_size > 2_000_000:
                raise ValueError('Snapshot file exceeds 2 MB')
            result = store_artifacts.import_snapshot(json.loads(args.file.read_text('utf-8-sig')))
        elif args.command == 'read-snapshot':
            result = store_artifacts.read_snapshot(args.store_id)
        else:
            result = store_artifacts.read_report(args.report_id)
    except (OSError, ValueError) as exc:
        parser.exit(1, f'{exc}\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
