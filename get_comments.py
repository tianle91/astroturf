import json
import os
import praw
from google.cloud import storage
from astroturf.prawtools import make_package_training


def upload_blob_if_not_exist(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket.
    # bucket_name = "your-bucket-name"
    # source_file_name = "local/path/to/file"
    # destination_blob_name = "storage-object-name"
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    if not blob.exists():
        blob.upload_from_filename(source_file_name)
        print("File {} uploaded to {}.".format(source_file_name, destination_blob_name))
    else:
        print("File {} exists! Skipped.".format(source_file_name))

def dump_user_comments(
    user_name, reddit, limit=1000,
    local_prefix='data/user/',
    gcp_bucket=None,
):
    '''dump user comments to {prefix}/{user_name}/*.json'''
    local_outpath = os.path.join(local_prefix, user_name)
    os.makedirs(local_outpath, exist_ok=True)
    i = 0
    for comment in reddit.redditor(user_name).comments.new(limit=limit):
        commentoutpath = os.path.join(local_outpath, '{}.json'.format(comment.id))
        print ('[{}/{}] id: {}, body: {}, commentoutpath: {}'.format(
            i, limit,
            comment.id,
            comment.body.replace('\n', ' ').replace('\t', ' ')[:50],
            commentoutpath
        ))
        i += 1
        if not os.path.isfile(commentoutpath):
            package = make_package_training(comment, reddit)
            with open(commentoutpath, 'w+') as f:
                json.dump(package, f, indent=4)
        if gcp_bucket:
            upload_blob_if_not_exist(
                gcp_bucket,
                source_file_name=commentoutpath,
                destination_blob_name=commentoutpath
            )
    return True

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='search comments by new for user.')
    parser.add_argument('--users', type=str, nargs='*')
    parser.add_argument('--limit', type=int, default=1000)
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
        print ('\n\nuser_name: {} running...\n\n'.format(user_name))
        status = dump_user_comments(user_name, reddit, limit=1000, gcp_bucket='astroturf-dev-data')
        print ('\n\nuser_name: {} done?: {}\n\n'.format(user_name, status))
