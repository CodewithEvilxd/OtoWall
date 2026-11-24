"""Allow ``python -m otowall``."""

import sys

if sys.platform == "win32":
    from otowall.platforms.windows_dpi import set_process_dpi_aware

    set_process_dpi_aware()

from otowall.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
