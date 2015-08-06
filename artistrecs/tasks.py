from __future__ import absolute_import, unicode_literals
import codecs
import json
import os

from celery.utils.log import get_task_logger

import spotipy

from . import settings as task_settings
from .models import SearchTypes
from .api import get_api_client
from .celery import app


logger = get_task_logger(__name__)


@app.task(queue='extraction')
def playlist_generator(term,
                       search_type=SearchTypes.query,
                       offset=0,
                       limit=task_settings.SPOTIFY_MAX_LIMIT):
    """Searches Spotify for playlists matching `term`.

    Args:
        term: String to use for Spotify playlist search
        offset: Search results offset
        limit: Limits playlist result count. Max 50.

    Returns:
        True if successful, otherwise False. Check logs for failure info.
    """

    if limit > task_settings.SPOTIFY_MAX_LIMIT:
        logger.warning('Forcibly resetting `limit` to {}'.format(
            task_settings.SPOTIFY_MAX_LIMIT))
        limit = task_settings.SPOTIFY_MAX_LIMIT

    api = get_api_client()

    logger.info('Searching for {} playlists / offset={} limit={}'.format(
        term, offset, limit
    ))

    # search spotify for a term
    if search_type == SearchTypes.Query:
        logger.debug('Querying user playlists for "{}"'.format(term))
        results = api.search(term, type='playlist', offset=offset,
                             limit=limit)
    if search_type == SearchTypes.Category:
        logger.debug('Querying category playlists for "{}"'.format(term))
        results = api.category_playlists(term, offset=offset, limit=limit)

    playlists = results['playlists']['items']

    if len(playlists) == 0:
        logger.warning('No playlists found for {}'.format(term))
        return False

    for playlist in playlists:
        resolve_playlist.delay(playlist['owner']['id'],
                               playlist['id'])

    return True


@app.task(queue='extraction')
def resolve_playlist(user_id, playlist_id):
    """Looks up tracks inside of a given Spotify playlist.

    Args:
        user_id: Spotify user id
        playlist_id: Spotify playlist id

    Returns:
        True if successful, otherwise False. Check logs for failure info.
    """

    api = get_api_client()

    # pull a playlist
    # NOTE: hardcoded limit of 50 tracks
    playlist_tracks = api.user_playlist_tracks(user_id, playlist_id, limit=50)
    playlist_label = '{}:{}'.format(user_id, playlist_id)

    logger.info('Found {} track(s) in {}'.format(
        len(playlist_tracks['items']),
        playlist_label
    ))

    artists = []

    for track in playlist_tracks['items']:
        for artist in track['track']['artists']:
            # naively protect sentence from whole albums
            # inside of a playlist.
            # NOTE: consider slicing off last 3-5 tracks
            #       and checking those.
            if len(artists) and artists[-1] == artist['name']:
                logger.debug('Rewind-based skip of duplicate '
                             'artist "{}" in {}'.format(
                    artist['name'],
                    playlist_label
                ))
                continue

            logger.debug('Adding {} to sentence'.format(artist['name']))
            artists.append(artist['name'])

    # fire off export task
    export_artist_sentence_from_playlist.delay(user_id, playlist_id, artists)


@app.task(queue='writer')
def export_artist_sentence_from_playlist(user_id,
                                         playlist_id,
                                         artist_sentence):
    """Extracts artist names from a Spotify playlist
    and returns a word2vec-ready list
    """

    output_path = os.path.realpath(os.environ['SENTENCE_OUTPUT_PATH'])

    obj = json.dumps({
        'user_id': user_id,
        'playlist_id': playlist_id,
        'sentence': artist_sentence,
    })

    codecs.open(output_path, 'a', encoding='utf-8').write(obj + '\n')

    logger.debug('Wrote sentence of length {}'.format(len(artist_sentence)))
