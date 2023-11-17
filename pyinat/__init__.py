# ruff: noqa: F401, F403
"""Namespace alias that combines modules from pyinaturalist and pyinaturalist-convert (if installed).
This allows abbreviated imports like::

    >>> from pyinat import iNatClient, to_csv, to_parquet

"""

from pyinaturalist import *

try:
    from pyinaturalist_convert import *
except ImportError:
    pass
