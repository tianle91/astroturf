import json
import os

import praw
from google.cloud import storage

from astroturf.prawtools import make_package_training

client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
path_config = json.loads(config_bucket.blob('pathConfig.json').download_as_string())
data_bucket = path_config['data_bucket']
data_path = path_config['data_path']


def refresh_user_comments(user_name: str, reddit: praw.Reddit, limit: int = 1000):
    '''dump user comments to {gcp_bucket}/{prefix}/{user_name}/{comment_id}.json'''

    bucket = client.bucket(data_bucket)
    cloud_data_path_user = os.path.join(data_path, user_name)
    exist_blob_paths = [blob.name for blob in client.list_blobs(bucket, prefix=cloud_data_path_user)]
    i = 0
    for comment in reddit.redditor(user_name).comments.new(limit=limit):
        blob_path = os.path.join(cloud_data_path_user, '{}.json'.format(comment.id))
        if not blob_path in exist_blob_paths:
            print('[{i}/{limit}] id: {id}, body: {body}'.format(
                i=i, limit=limit, id=comment.id, body=comment.body.replace('\n', ' ').replace('\t', ' ')[:50]
            ))
            package = make_package_training(comment, reddit)
            blob = bucket.blob(blob_path)
            blob.upload_from_string(json.dumps(package, indent=4))
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
        print('user_name: {} running...'.format(user_name))
        status = refresh_user_comments(user_name, reddit, limit=100)
