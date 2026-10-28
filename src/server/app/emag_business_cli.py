"""Collect selected eMAG RO inventory/order/return/invoice evidence without writes."""
import argparse,json
import httpx
from app.services import emag_business,emag_readonly
from app.services.windows_credentials import read_emag_credentials
from app.services.store_artifacts import validate_id


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store-id',required=True)
    parser.add_argument('--days',type=int,default=29,choices=range(1,30))
    args=parser.parse_args(argv)
    try:
        validate_id(args.store_id)
        user,password=read_emag_credentials()
    except (ValueError,OSError,UnicodeError):
        print('Invalid store label or configured credential unavailable.');return 2
    try:
        with httpx.Client(timeout=35,follow_redirects=False) as client:
            evidence=emag_business.collect(client,httpx.BasicAuth(user,password),args.days)
        evidence=emag_readonly.redact(evidence,(user,password))
    except (ValueError,httpx.HTTPError,ImportError):
        print('Read-only collection incomplete; no snapshot imported.');return 1
    finally:
        del user,password
    try:snapshot=emag_business.publish(args.store_id,evidence)
    except (ValueError,OSError):
        print('Local snapshot save failed; check data directory and artifact size.');return 2
    print(json.dumps({'snapshot_id':snapshot['snapshot_id'],'summary':evidence['summary']},ensure_ascii=False))
    return 0


if __name__=='__main__':raise SystemExit(main())
