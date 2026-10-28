"""Inspect/record manual operations. This CLI never writes to eMAG."""
import argparse
import getpass
import json
from app.services import emag_operations


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store-id',required=True)
    parser.add_argument('--snapshot-id')
    parser.add_argument('--issue-id')
    parser.add_argument('--state',choices=emag_operations.STATES[1:])
    parser.add_argument('--revision',type=int)
    parser.add_argument('--note')
    parser.add_argument('--review-snapshot-id')
    args=parser.parse_args(argv)
    if any(x is not None for x in (args.snapshot_id,args.issue_id,args.state,args.revision,args.note,args.review_snapshot_id)):
        if not all(x is not None for x in (args.snapshot_id,args.issue_id,args.state,args.revision,args.note)):
            parser.error('Transitions require snapshot, issue, state, revision and note')
        try: result=emag_operations.transition(args.store_id,args.snapshot_id,args.issue_id,args.state,args.revision,args.note,getpass.getuser(),args.review_snapshot_id)
        except (ValueError,OSError):
            print('Transition rejected; reload evidence and check state/revision.');return 1
    else:
        try: result=emag_operations.board(args.store_id)
        except (ValueError,OSError):
            print('No valid eMAG RO snapshot.');return 1
    print(json.dumps(result,ensure_ascii=False));return 0


if __name__=='__main__':raise SystemExit(main())
