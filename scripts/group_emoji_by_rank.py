#!/usr/bin/env python
"""Take a flat dict of taxon IDs and emoji, and group them into sub-dicts by taxon rank.
This makes it much simpler to look up the most specific (lowest rank level) emoji for a given
taxon based on its ancestry.
"""
from os.path import dirname, join

import toml

from pyinaturalist import Taxon, get_taxa_by_id, pprint

CONFIG_FILE = join(dirname(__file__), 'emoji.toml')


def group_emoji_by_rank():
    with open(CONFIG_FILE) as f:
        config = toml.load(f)
        emoji = {int(k): v for k, v in config['EMOJI'].items()}

    print(f'Looking up {len(emoji)} taxa...')
    taxa = Taxon.from_json_list(get_taxa_by_id(list(emoji.keys())))
    pprint(taxa)

    rank_levels = {t.id: t.rank_level for t in taxa}
    emoji_by_rank = {rank: {} for rank in rank_levels.values()}

    for taxon_id, char in emoji.items():
        rank = rank_levels[taxon_id]
        emoji_by_rank[rank][taxon_id] = char
    return {k: emoji_by_rank[k] for k in sorted(emoji_by_rank)}


if __name__ == '__main__':
    print(group_emoji_by_rank())
