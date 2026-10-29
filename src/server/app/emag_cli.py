"""Collect eMAG RO offers: python -m app.emag_cli --store-id my-store-ro."""
import argparse
import getpass
from datetime import datetime, timezone
import json
import sys

import httpx
from app.services import emag_readonly as emag
from app.services.store_artifacts import validate_id
from app.services.windows_credentials import read_emag_credentials


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store-id', help='Local evidence label, not an API account identifier')
    parser.add_argument('--sku', help='Read one exact SKU without importing a store snapshot')
    parser.add_argument('--prompt', action='store_true', help='Use local hidden input instead of Windows credentials')
    parser.add_argument('--describe', action='store_true', help='Describe requests without reading credentials or connecting')
    args = parser.parse_args(argv)
    if args.describe:
        if args.sku is not None:
            print(json.dumps({'endpoint': emag.ENDPOINT, 'method': 'POST', 'filter': 'part_number',
                              'scope': 'single_sku_read_only', 'credential_target': 'IvyeaOps/eMAG/RO',
                              'writes': 'none'}))
        else:
            print(json.dumps({'endpoint': emag.ENDPOINT, 'method': 'POST', 'page_size': 100,
                              'max_pages': 100, 'delay_seconds': 1, 'credential_target': 'IvyeaOps/eMAG/RO',
                              'writes': 'local snapshot and report only'}))
        return 0
    try:
        if args.sku is not None:
            if args.store_id is not None or not args.sku.strip() or len(args.sku) > 256 or any(ord(c) < 32 or ord(c) == 127 for c in args.sku):
                raise ValueError('Invalid SKU or incompatible store ID')
        else:
            validate_id(args.store_id)
        if args.prompt:
            if not sys.stdin.isatty():
                raise ValueError('Interactive terminal required')
            username = input('eMAG API username: ').strip()
            password = getpass.getpass('eMAG API password (hidden): ')
        else:
            username, password = read_emag_credentials()
        if not username or not password:
            raise ValueError('Empty credentials')
    except (OSError, ValueError, UnicodeError):
        print('Store ID or credentials unavailable; no request sent. Check --help and the configured credential.', file=sys.stderr)
        return 2
    try:
        with httpx.Client(timeout=30, follow_redirects=False,
                          headers={'User-Agent': 'IvyeaOps-ReadOnly/1.0'}) as client:
            auth = httpx.BasicAuth(username, password)
            result = emag.lookup_sku(client, auth, args.sku) if args.sku is not None else emag.collect(client, auth)
            if args.sku is not None:
                result['offer'] = emag.redact_values(result['offer'], (username, password))
            else:
                result = emag.redact(result, (username, password))
            del auth
    except (httpx.HTTPError, ImportError, ValueError):
        print('Transport setup failed. Check proxy dependencies and connectivity.', file=sys.stderr)
        return 2
    finally:
        del username, password
    if args.sku is not None:
        print(json.dumps({'source': emag.ENDPOINT, 'captured_at': datetime.now(timezone.utc).isoformat(),
                          'scope': 'single_sku_read_only', **result}, ensure_ascii=False))
        return 1 if result['status'] == 'incomplete' else 0
    if not result['complete']:
        print(json.dumps({'complete': False, 'reason': result['reason'], 'records_read': len(result['offers']),
                          'imported': False}))
        return 1
    try:
        receipt = emag.publish(args.store_id, result)
    except (OSError, ValueError):
        print('Local artifact save failed. Check data directory and the 2 MB artifact limit.', file=sys.stderr)
        return 2
    print(json.dumps(receipt))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
