"""Functions to help load and import CSV files"""
# TODO: There are lots of other things that could go in this category. Either these should be
#   kept simple, or moved to a separate repo.
from glob import glob
from logging import getLogger
from os.path import basename, expanduser
from typing import Iterable, List

from pyinaturalist.constants import ResponseObject
from pyinaturalist.formatters import simplify_observation

logger = getLogger(__name__)


def load_exports(*file_paths: str):
    """Combine multiple exported CSV files into one, and return as a dataframe"""
    import pandas as pd

    resolved_paths = resolve_file_paths(*file_paths)
    logger.info(
        f'Reading {len(resolved_paths)} exports:\n'
        + '\n'.join([f'\t{basename(f)}' for f in resolved_paths])
    )

    df = pd.concat((pd.read_csv(f) for f in resolved_paths), ignore_index=True)
    return df


def resolve_file_paths(*file_paths: str) -> List[str]:
    """Given a list of file paths and/or glob patterns, return a list of resolved file paths"""
    resolved_paths = [p for p in file_paths if '*' not in p]
    for path in [p for p in file_paths if '*' in p]:
        resolved_paths.extend(glob(path))
    return [expanduser(p) for p in resolved_paths]


def to_dataframe(observations: Iterable[ResponseObject]):
    """Normalize observation JSON into a DataFrame"""
    import pandas as pd

    return pd.json_normalize([simplify_observation(obs) for obs in observations])
