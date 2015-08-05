#!/usr/bin/env python

"""
Passes extraction output into `word2vec`
and prints results as JSON.
"""

from __future__ import absolute_import, unicode_literals
import json

import click

from numpy import array as np_array

import gensim


class LineGenerator(object):
    """Reads a sentence file, yields numpy array-wrapped sentences
    """

    def __init__(self, fh):
        self.fh = fh

    def __iter__(self):
        for line in self.fh.readlines():
            yield np_array(json.loads(line)['sentence'])


def serialize_rankings(rankings):
    """Returns a JSON-encoded object representing word2vec's
    similarity output.
    """

    return json.dumps([
        {'artist': artist, 'rel': rel}
        for (artist, rel)
        in rankings
    ])


@click.command()
@click.option('-i', 'input_file', type=click.File('r', encoding='utf-8'),
              required=True)
@click.option('-t', 'term', required=True)
@click.option('--min-count', type=click.INT, default=5)
@click.option('-w', 'workers', type=click.INT, default=4)
def cli(input_file, term, min_count, workers):
    # create word2vec
    model = gensim.models.Word2Vec(min_count=min_count, workers=workers)
    model.build_vocab(LineGenerator(input_file))

    try:
        similar = model.most_similar(term)
        click.echo( serialize_rankings(similar) )
    except KeyError:
        # really wish this was a more descriptive error
        exit('Could not parse input: {}'.format(exc))


if __name__ == '__main__':
    cli()
