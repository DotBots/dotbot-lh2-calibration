"""DotBot LH2 calibration Python tooling — DEPRECATED.

The Python side of this package (TUI + exporter) has been folded into
the unified ``dotbot`` package as of 2026-05. Migrate with::

    pip install dotbot[calibrate]
    dotbot calibrate           # the TUI
    dotbot calibrate export    # the C-header exporter

The C firmware in ``calibration/`` continues to live here and is not
affected by this deprecation.

This standalone Python package will be archived after a 6-month
grace period. See https://github.com/DotBots/PyDotBot.
"""

import sys
import warnings

_DEPRECATION_MESSAGE = (
    "dotbot-lh2-calibration's Python side is deprecated; use "
    "`pip install dotbot[calibrate]` and `dotbot calibrate ...` "
    "(or `dotbot calibrate export ...`) instead. "
    "The C firmware in this repo is unaffected. "
    "This standalone Python package will be archived after 2026-11."
)

warnings.warn(_DEPRECATION_MESSAGE, DeprecationWarning, stacklevel=2)
# Print to stderr too — DeprecationWarning is silenced by default for
# end users running the CLI, and we want them to see this.
print(f"[DEPRECATION] {_DEPRECATION_MESSAGE}", file=sys.stderr)
