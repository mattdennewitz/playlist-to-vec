from __future__ import absolute_import, unicode_literals
import os

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from .settings import SPOTIFY_MAX_LIMIT


class SpotifyWrapper(spotipy.Spotify):
    def category_playlists(self, category, limit=SPOTIFY_MAX_LIMIT, offset=0):
        return self._get('browse/categories/%s/playlists' % category,
                         limit=limit,
                         offset=offset)


def get_api_client():
    # create a client authentication request
    client_cred = SpotifyClientCredentials(
        client_id=os.environ['SPOTIFY_CLIENT_ID'],
        client_secret=os.environ['SPOTIFY_CLIENT_SECRET']
    )

    # create a spotify client with a bearer token,
    # dynamically re-created if necessary
    return SpotifyWrapper(auth=client_cred.get_access_token())
