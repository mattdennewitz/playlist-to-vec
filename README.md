# artistrecs

A similar artist recommendation engine powered by Spotify
playlists and [word2vec](https://code.google.com/p/word2vec/).

This proof of concept was inspired by two pieces and my own
longstanding belief that the transitions between songs in playlists,
when given enough, are valuable insights.

Some bathroom reading:

- [Playlist Harvesting](https://social.shorthand.com/huntedguy/3CfQA8mj2S/playlist-harvesting),
  by [Stephen Phillips](https://social.shorthand.com/huntedguy)
- [Distributional Similarity Music Recommendations Versus Spotify: A Comparison Based on User Evaluation](http://arno.uvt.nl/show.cgi?fid=136352), by Nevyana Boycheva

Also, quick reminder: this is a proof of concept! It's working and
pretty cool, but that doesn't mean the tools are complete, the project
isn't without layout or design decision kinks, or that things won't change.
In fact, plan on things changing for as long as this message is here.

----

This application consists of two major components:

- A Celery-backed extraction setup for ingesting playlists from Spotify
  en masse. Celery workers are responsible for importing playlists
  and extracting artist names.
- Helper scripts for training and querying data extracted
  from said playlists

**NOTE** - project layout will be changing shortly. See TODO for what's up.

## Setup

Before getting started with this project, please ensure you have the
following installed:

- a C compiler
- Redis (up and running)
- [`word2vec` bindings](#install-word2vec)

Please also have your OAuth client ID and secret ready from
the Spotify application you wish to use. If you need to register
a Spotify app, [do so here](https://developer.spotify.com/my-applications/#!/applications/create) before continuing.

### Install `word2vec` bindings

<a name="install-word2vec"></a>

#### OSX using Homebrew

```shell
$ brew install --HEAD homebrew/head-only/word2vec
```

### Setup

### Install requirements

Check out this repo into a virtualenv,
and then install its Python requirements using `pip`:

```shell
$ pip install -r requirements.txt
```

### Set up environment variables

This application's configuration data is taken from environment variables.

- `SPOTIFY_CLIENT_ID`: Spotify OAuth client id
- `SPOTIFY_CLIENT_SECRET`: Spotify OAuth client secret
- `ARTISTRECS_BROKER_URL`: Celery broker URL.
    Defaults to `localhost:6379`. [Read more](http://docs.celeryproject.org/en/latest/configuration.html#broker-url).
- `ARTISTRECS_RESULT_BACKEND`: Celery result backend URL.
    Defaults to `localhost:6379` [Read more](http://docs.celeryproject.org/en/latest/configuration.html#celery-result-backend)

How you set these variables is up to you.

**TIP**: `envdir` is great for this.

## Workflow and output

### Extraction workflow

First, a quick overview of what the Celery workers are doing,
from start to finish:

1. `playlist_generator` task receives a request to search Spotify's playlists
   for a specific term. For each playlist found, `playlist_generator`
   creates a new task: `resolve_playlist`.

   If `recycle` is enabled, `playlist_generator` will respawn itself
   to collect more information. This is controlled by the `max_recycles`
   parameter - if left undefined, `playlist_generator` will collect
   all playlists available for the given term.
2. `resolve_playlist` receives a username and playlist id and fetches
   the playlist's tracks. It then compiles into a list each artist name
   from each track in the playlist [1]. Once all names have been collected,
   `resolve_playlist` hands off the list to
   `export_artist_sentence_from_playlist`.
3. `export_artist_sentence_from_playlist` accepts a user id, playlist id,
   and a list of artist names. It JSON-encodes them and then writes
   the object to a file.

   This task is run in a separate queue to avoid overlapping file writes.

Once all jobs have been processed, you should have a text file
ready to be processed by the `parser.py` script.

[1] If the artist name about to be collected is also the last entry
    in the current list, it is ignored. This is a naive way of protecting
    against entire albums influencing transitional frequencies.

Right now, there are many moving pieces. As this project matures
past "proof of concept", noise will be reduced.

### Output format

`word2vec` works by analyzing sentences. That's a gross generalization.
Here's something from the official docs:

> The word2vec tool takes a text corpus as input and produces the word vectors as output. It first constructs a vocabulary from the training text data and then learns vector representation of words. The resulting word vector file can be used as features in many natural language processing and machine learning applications.

`gensim`, the `word2vec` implementation used here, expects sentences
to be delivered as lists of words. In our particular use case,
we're constructing sentences from artist names. Wild, right?

At the end of a run thorugh the extraction workflow described above,
you'll have a file whose every line has a sentence constructed from artists
in a playlist. The format for this output is:

```json
{
    "playlist_id": "<spotify playlist id>",
    "user_id": "<spotify user id>",
    "sentence": [
        "<artist name>",
        "<artist name>",
        ...
    ]
}
```

This file can be found at `SENTENCE_OUTPUT_PATH`.

## Running

Once you've completed the above, you're ready to begin.

### Start Redis

If `redis-server` is not already running in the background, fire it up.

```shell
$ redis-server
```

### Start extraction queues

In one shell inside your virtualenv, fire up the extraction queue.
This queue is responsible for the tasks concerned with querying 
Spotify and compiling artist names from tracks inside of playlists.

```shell
$ celery worker -A artistrecs -l info -Q extraction
```

In another shell, start the writer queue with 1 worker. This is a sloppy
workaround to prevent overlapping file writes by unlocked append access
to a file.

```shell
$ celery worker -A artistrecs -l info -Q writer
```

### Insert a task

To query Spotify for playlists, insert a task using `insert_task.py`.
This helper script accepts two parameters, expecting one of them:

```shell
$ python insert_task.py -t <term>
```

See `insert_task.py`'s `--help` print-out for extended usage details.

### Parsing output

Data extracted from playlists may be parsed using `parser.py`.

```shell
$ python parser.py -i <path to output file> -t <artist name>
```

This will emit a JSON-encoded ranked list of similar artists.
Make sure that the artist name you're checking was, in fact,
a member of at least a few of the playlists brought in during
extraction.

See `--help` for extended usage details.

## TODO

- Add `setup.py`, which should also install helper scripts as console scripts
- Parser should default to using `SENTENCE_OUTPUT_PATH` env var
  when `-i` is not given.

## Issues

Want to contribute? File an issue or a pull request.
