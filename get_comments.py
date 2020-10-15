import json
import os
import praw
from google.cloud import storage
from astroturf.prawtools import make_package_training


def dump_user_comments(
    user_name, reddit, limit=1000,
    local_prefix='data/user/',
    gcp_bucket='astroturf-dev-data',
):
    '''dump user comments to {prefix}/{user_name}/*.json and gcp_bucket'''
    local_outpath = os.path.join(local_prefix, user_name)
    os.makedirs(local_outpath, exist_ok=True)
    gcp_storage_client = storage.Client()
    gcp_bucket = gcp_storage_client.bucket(gcp_bucket)

    i = 0
    for comment in reddit.redditor(user_name).comments.new(limit=limit):
        commentoutpath = os.path.join(local_outpath, '{}.json'.format(comment.id))
        print ('[{i}/{limit}] id: {id}, body: {body}'.format(
            i=i, limit=limit, id=comment.id, body=comment.body.replace('\n', ' ').replace('\t', ' ')[:50]
        ))
        # ensure local_exists
        local_exists = os.path.isfile(commentoutpath)
        if not local_exists:
            package = make_package_training(comment, reddit)
            with open(commentoutpath, 'w+') as f:
                json.dump(package, f, indent=4)
        # ensure cloud_exists
        gcp_blob = gcp_bucket.blob(commentoutpath)
        if not gcp_blob.exists():
            gcp_blob.upload_from_filename(commentoutpath)
        i += 1
    return True

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='search comments by new for user.')
    parser.add_argument('--users', type=str, nargs='*')
    parser.add_argument('--limit', type=int, default=100)
    args = parser.parse_args()

    limit = args.limit
    reddit = praw.Reddit()
    
    # list of users
    if args.users is None:
        with open('users.txt') as f:
            users = f.read().split()
    else:
        users = list(args.users)

    for user_name in users:
        print ('user_name: {} running...'.format(user_name))
        status = dump_user_comments(user_name, reddit, limit=100)
