import pandas as pd
from datetime import datetime
import os
import json
import pickle
import praw


def get_context(comment, reddit):
    submission = reddit.submission(id=comment.link_id.replace('t3_', ''))
    parent_comment = None
    if not comment.parent_id == comment.link_id:
        # not a top level comment, try to retrieve parent comment
        parent_comment = reddit.comment(id=comment.parent_id.replace('t1_', ''))
    return parent_comment, submission

def get_all_context(comment, reddit):
    parent_comment, submission = get_context(comment, reddit)
    if parent_comment is None:
        # base case: is a top level comment
        parent_comments = []
        return parent_comments, submission
    else:
        parent_comments, submission = get_all_context(parent_comment, reddit)
        return (parent_comments + [parent_comment], submission)

def format_comment_as_json(comment):
    return {
        'id': comment.id, 
        'author': comment.author.name if comment.author is not None else None, 
        'body': comment.body, 
        'created_utc': comment.created_utc,
        'permalink': comment.permalink,
    }

def format_submission_as_json(submission):
    return {
        'id': submission.id,
        'subreddit': submission.subreddit.display_name,
        'title': submission.title,
        'selftext': submission.selftext,
        'permalink': submission.permalink,
        
    }

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='search comments by new for user.')
    parser.add_argument('--user', type=str, default='suncoasthost')
    parser.add_argument('--limit', type=int, default=1000)
    args = parser.parse_args()

    user_name = args.user
    limit = args.limit

    reddit = praw.Reddit()
    user = reddit.redditor(user_name)

    outpath = 'data/user/{}'.format(user_name)
    os.makedirs(outpath, exist_ok=True)

    manifestpath = os.path.join('data/user/{}/manifest.csv'.format(user_name))
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
