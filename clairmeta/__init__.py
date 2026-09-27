# Clairmeta - (C) YMAGIS S.A.
# See LICENSE for more information

from clairmeta.dcp import DCP
from clairmeta.info import __author__, __license__, __version__
from clairmeta.logger import get_log
from clairmeta.sequence import Sequence
from clairmeta.utils.probe import PROBE_DEPS, check_command

__all__ = ["DCP", "Sequence"]
__license__ = __license__
__author__ = __author__
__version__ = __version__


# External dependencies check
for d in PROBE_DEPS:
    if not check_command(d):
        get_log().warning(f"Missing dependency : {d}")
