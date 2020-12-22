import json

import requests
from google.cloud import pubsub_v1, storage

from scraper import refresh_user_comments_cloud
from trainer import refresh_finetuned_cloud

# some clients and variables
client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
path_config = json.loads(config_bucket.blob(
    'pathConfig.json').download_as_string())
project_id = path_config['project_id']
infer_endpoint = path_config['infer_endpoint']

# subscribing to refresh requests
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(
    project_id, path_config['sub_update_request'])

if __name__ == '__main__':
    import argparse

    from praw_utils import get_reddit

    parser = argparse.ArgumentParser(
        description='search comments by new for user.')
    parser.add_argument('--limit', type=int, default=100)
    parser.add_argument('--blocksize', type=int, default=16)
    parser.add_argument('--maxsteps', type=int, default=10)
    parser.add_argument('--forceupdate', type=bool, default=False)
    args = parser.parse_args()

    reddit = get_reddit(client, 'astroturf-dev-configs')

    while True:
        print('Listening')
        response = subscriber.pull(
            request={"subscription": subscription_path, "max_messages": 1})

        username = None
        for msg in response.received_messages:
            username = msg.message.data.decode('utf-8')
            print(f"Received message: {username}")

        ack_ids = [msg.ack_id for msg in response.received_messages]
        if len(ack_ids) > 0 and username is not None:
            # there's something to do! ack it to remove from queue.
            subscriber.acknowledge(
                request={"subscription": subscription_path, "ack_ids": ack_ids})
            # update comments
            refreshed_comment_ids = refresh_user_comments_cloud(
                username, reddit, limit=args.limit)
            if len(refreshed_comment_ids) > 0:
                # update finetuned
                username_finedtuned = refresh_finetuned_cloud(
                    username,
                    blocksize=args.blocksize,
                    maxsteps=args.maxsteps,
                    force_update=args.forceupdate
                )
                # update model at infer endpoint
                inferresponse = requests.get('{infer_endpoint}/{username}?refresh=True'.format(
                    infer_endpoint=infer_endpoint,
                    username=username
                )).json()
