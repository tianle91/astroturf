import json
import os

import praw
from google.cloud import storage

from astroturf.prawtools import make_package_training
from statusflags import StatusFlags

client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
path_config = json.loads(config_bucket.blob('pathConfig.json').download_as_string())
data_bucket = client.bucket(path_config['data_bucket'])
status_bucket = client.bucket(path_config['status_bucket'])


def refresh_user_comments(user_name: str, reddit: praw.Reddit, limit: int = 1000):
    '''dump user comments to {gcp_bucket}/{prefix}/{user_name}/{comment_id}.json'''
    status_progress = status_bucket.blob(os.path.join(user_name, StatusFlags.data_refresh_progress))
    status_progress.upload_from_string('starting')
    exist_blob_paths = [blob.name for blob in client.list_blobs(data_bucket, prefix=user_name)]
    i = 0
    for comment in reddit.redditor(user_name).comments.new(limit=limit):
        blob_path = os.path.join(user_name, '{}.json'.format(comment.id))
        if not blob_path in exist_blob_paths:
            status_str = '[{i}/{limit}] id: {id}, body: {body}'.format(
                i=i, limit=limit, id=comment.id, body=comment.body.replace('\n', ' ').replace('\t', ' ')[:50]
            )
            print(status_str)
            package = make_package_training(comment, reddit)
            blob = data_bucket.blob(blob_path)
            blob.upload_from_string(json.dumps(package, indent=4))
        i += 1
    status_progress.delete()
    status_success = status_bucket.blob(os.path.join(user_name, StatusFlags.data_refresh_success))
    status_success.upload_from_string('done')
    return True


if __name__ == '__main__':

    import argparse
    from praw_utils import get_reddit

    parser = argparse.ArgumentParser(description='search comments by new for user.')
    parser.add_argument('--users', type=str, nargs='*')
    parser.add_argument('--limit', type=int, default=100)
    args = parser.parse_args()

    limit = args.limit
    reddit = get_reddit(client, 'astroturf-dev-configs')

    # list of users
    if args.users is None:
        with open('users.txt') as f:
            users = f.read().split()
    else:
        users = list(args.users)

    for user_name in users:
        print('user_name: {} running...'.format(user_name))
        status = refresh_user_comments(user_name, reddit, limit=args.limit)
