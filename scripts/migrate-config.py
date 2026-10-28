"""Copy an ignored legacy source .env only when the new file does not exist."""
import argparse
from pathlib import Path
import shutil
import os
import secrets


def migrate(root):
    root=Path(root).resolve()
    old=root/'server'/'.env'
    new=root/'src'/'server'/'.env'
    if new.exists():return 'existing'
    if not old.is_file():return 'absent'
    new.parent.mkdir(parents=True,exist_ok=True)
    temporary=new.with_name('.env.migrating-'+secrets.token_hex(8))
    try:
        shutil.copy2(old,temporary)
        os.link(temporary,new)  # Atomic no-clobber publication on the same volume.
    except FileExistsError:
        return 'existing'
    finally:
        temporary.unlink(missing_ok=True)
    return 'migrated'


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True)
    migrate(parser.parse_args().root)
