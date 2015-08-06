#!/usr/bin/env python

"""
Begin an Spotify playlist extraction job.

Basic Usage:

    Usage: insert_task.py [OPTIONS]

    Options:
      -t TEXT     Search term  [required]
      -o INTEGER  Search results offset
      -l INTEGER  Per-page limit. Max/default is 50.
      -c INTEGER  Total number of playlists desired.
      --help      Show this message and exit.
"""

from __future__ import absolute_import, unicode_literals
import math

import click

from artistrecs import settings as ex_settings
from artistrecs.models import SearchTypes
from artistrecs.tasks import playlist_generator


@click.command()
@click.option('-s', 'search_type', help='Search type',
              type=click.Choice([m.name for m in SearchTypes]),
              default=SearchTypes.query)
@click.option('-t', 'term', required=True, help='Search term')
@click.option('-o', 'offset', type=click.INT, default=0,
              help='Search results offset')
@click.option('-l', 'per_page', type=click.INT,
              default=ex_settings.SPOTIFY_MAX_LIMIT,
              help='Per-page limit. Max/default is 50.')
@click.option('-c', 'total_objects', type=click.INT, default=50,
              help='Total number of playlists desired.')
def insert_task(search_type, term, offset, per_page, total_objects):
    """Spawns an extraction task

    Args:
        search_type: One of 'category' or 'query', used to determine
            what kind of playlist search should be performed
        term: Search term, e.g., "Coltrane Motion"
        offset: Resultset offset
        limit: Maximum number of results to be returned per page.
            Max allowed value by Spotify is 50.
        total_objects: The maximum number of playlists you'd like to process
    """

    search_type = getattr(SearchTypes, search_type)

    if per_page > ex_settings.SPOTIFY_MAX_LIMIT:
        per_page = ex_settings.SPOTIFY_MAX_LIMIT

    prange = int( math.ceil( float(total_objects) / per_page ) )

    if per_page > total_objects:
        per_page = total_objects

    if prange == 0:
        exit('No pages to scrape with given limit')

    click.echo('Fetching up to {} playlists matching "{}"'.format(
        total_objects, term))

    for page_number in range(prange):
        next_offset = page_number * per_page
        playlist_generator.delay(term, search_type,
                                 offset=next_offset, limit=per_page)

        click.echo('Inserted "{}" for extraction / offset={} limit={}'.format(
            term, next_offset, per_page))


if __name__ == '__main__':
    insert_task()
