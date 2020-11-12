import json

from flask import Flask
from google.cloud import pubsub_v1
from google.cloud import storage

from refresh_comments import refresh_user_comments
from refresh_finetuned import refresh_finetuned

app = Flask(__name__)

# some clients and variables
client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')

# subscribing to refresh requests
path_config = json.loads(config_bucket.blob('pathConfig.json').download_as_string())
project_id = path_config['project_id']
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, 'model_refresh_servicer')

if __name__ == '__main__':
    import argparse
    from praw_utils import get_reddit

    parser = argparse.ArgumentParser(description='search comments by new for user.')
    parser.add_argument('--limit', type=int, default=100)
    parser.add_argument('--blocksize', type=int, default=16)
    parser.add_argument('--maxsteps', type=int, default=10)
    parser.add_argument('--forceupdate', type=bool, default=False)
    args = parser.parse_args()

    reddit = get_reddit(client, 'astroturf-dev-configs')

    while True:
        print('Listening')
        response = subscriber.pull(request={"subscription": subscription_path, "max_messages": 1})
        for msg in response.received_messages:
            user_name = msg.message.data.decode('utf-8')
            print("Received message:", user_name)

        ack_ids = [msg.ack_id for msg in response.received_messages]
        if len(ack_ids) > 0:
            # there's something to do!
            # ack the message first
            subscriber.acknowledge(request={"subscription": subscription_path, "ack_ids": ack_ids})
            print('ack_ids: {}'.format(ack_ids))
            # run the updates
            print ('\nrefresh_user_comments...\n')
            status = refresh_user_comments(user_name, reddit, limit=args.limit)
            print ('\nrefresh_finetuned...\n')
            ran = refresh_finetuned(user_name, blocksize=args.blocksize, maxsteps=args.maxsteps,
                                    force_update=args.forceupdate)
