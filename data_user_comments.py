import pandas as pd
from datetime import datetime
import os
import json
import pickle
import praw

from astroturf.prawtools import get_context, format_comment_as_json, format_submission_as_json

def dump_user_comments(user_name, reddit, limit=1000):
    '''
    dump user comments to data/user/{user_name}/*.json
    and update data/user/{user_name}/manifest.csv with status
    '''
    user = reddit.redditor(user_name)
    outpath = 'data/user/{}'.format(user_name)
    os.makedirs(outpath, exist_ok=True)

    manifestpath = os.path.join(outpath, 'manifest.csv')
    if not os.path.isfile(manifestpath):
        manifestdf = None
        with open(manifestpath, 'w+') as f:
            f.write('comment_id, created_utcnow_isoformat\n')
    else:
        manifestdf = pd.read_csv(manifestpath)

    # args for user.comments.new()
    # https://praw.readthedocs.io/en/latest/code_overview/other/listinggenerator.html#praw.models.ListingGenerator
    # limit – default 100, max 1000    
    i = 0
    for comment in user.comments.new(limit=limit):
        print ('[{}/{}] id: {}, body: {}'.format(
            i, limit, comment.id, comment.body.replace('\n', ' ').replace('\t', ' ')[:50]
        ))
        i += 1
        if manifestdf is not None and comment.id in list(manifestdf['comment_id']):
            print ('skip since comment dump exists...')
            continue
        else:
            parent_comment, submission = get_context(comment, reddit)
            package = {
                'comment': format_comment_as_json(comment),
                'parent_comment': format_comment_as_json(parent_comment) if parent_comment is not None else None,
                'submission': format_submission_as_json(submission)
            }
            with open(manifestpath, 'a+') as f:
                f.write('{}, {}\n'.format(comment.id, datetime.utcnow().isoformat()))
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
        print ('\n\nuser_name: {} done?: {}\n\n'.format(user_name, dump_user_comments(user_name, reddit, limit=1000)))
