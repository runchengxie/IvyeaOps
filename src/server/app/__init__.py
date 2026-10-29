"""IvyeaOps backend package."""
import sys

if sys.version_info < (3, 11):
    raise RuntimeError("Python 3.11 or newer is required; update Python and recreate the server virtual environment.")
