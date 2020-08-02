import json
import os
import pickle
from datetime import datetime
from glob import glob

import pandas as pd
import praw

from astroturf.prawtools import (format_comment_as_json,
                                 format_submission_as_json, get_context,
                                 make_package_training)


def dump_user_comments(user_name, reddit, limit=1000, prefix='data/user/'):
    '''
    dump user comments to data/user/{user_name}/*.json
    and update data/user/{user_name}/manifest.csv with status
    '''
    outpath = os.path.join(prefix, user_name)
    os.makedirs(outpath, exist_ok=True)
    existingids = [s.replace(outpath, '').replace('.json', '') for s in glob(os.path.join(outpath, '*.json'))]
    i = 0
    for comment in reddit.redditor(user_name).comments.new(limit=limit):
        print ('[{}/{}] id: {}, body: {}'.format(
            i, limit, comment.id, comment.body.replace('\n', ' ').replace('\t', ' ')[:50]
        ))
        i += 1
        if comment.id in existingids:
            print ('skip since comment dump exists...')
            continue
        else:
            package = make_package_training(comment, reddit)
            with open(os.path.join(outpath, '{}.json'.format(comment.id)), 'w+') as f:
                json.dump(package, f, indent=4)
    return True


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='search comments by new for user.')
    parser.add_argument('--users', type=str, nargs='*')
    parser.add_argument('--limit', type=int, default=1000)
    args = parser.parse_args()

    limit = args.limit
    reddit = praw.Reddit()
    for user_name in args.users:
        print ('\n\nuser_name: {} running...\n\n'.format(user_name))
        status = dump_user_comments(user_name, reddit, limit=1000)
        print ('\n\nuser_name: {} done?: {}\n\n'.format(user_name, status))
