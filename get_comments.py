import json
import os
import praw
from google.cloud import storage
from astroturf.prawtools import make_package_training


def dump_user_comments(
    user_name, reddit, limit=1000,
    prefix='prawtools/make_package_training/user/',
    bucket='astroturf-dev-data',
):
    '''dump user comments to gcp_bucket/{prefix}/{user_name}/{comment_id}.json and '''
    client = storage.Client()
    bucket = client.bucket(bucket)
    prefix_user = os.path.join(prefix, user_name)
    exist_blob_names = [blob.name for blob in client.list_blobs(bucket, prefix=prefix_user)]
    i = 0
    for comment in reddit.redditor(user_name).comments.new(limit=limit):
        commentoutpath = os.path.join(prefix_user, '{}.json'.format(comment.id))
        print ('[{i}/{limit}] id: {id}, body: {body}'.format(
            i=i, limit=limit, id=comment.id, body=comment.body.replace('\n', ' ').replace('\t', ' ')[:50]
        ))
        if not commentoutpath in exist_blob_names:
            package = make_package_training(comment, reddit)
            gcp_blob = bucket.blob(commentoutpath)
            gcp_blob.upload_from_string(json.dumps(package, indent=4))
            print ('id: {id} Uploaded!'.format(id=comment.id))
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
