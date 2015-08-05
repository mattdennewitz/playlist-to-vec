import os

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


def get_api_client():
    # create a client authentication request
    client_cred = SpotifyClientCredentials(
        client_id=os.environ['SPOTIFY_CLIENT_ID'],
        client_secret=os.environ['SPOTIFY_CLIENT_SECRET']
    )

    # create a spotify client with a bearer token,
    # dynamically re-created if necessary
    return spotipy.Spotify(auth=client_cred.get_access_token())
