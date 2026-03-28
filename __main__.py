"""Package entry point for AI Image Workbench."""

from pathlib import Path
import sys

PACKAGE_DIR = Path(__file__).resolve().parent
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from main import main


if __name__ == "__main__":
    main()