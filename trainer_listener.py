import json

from google.cloud import pubsub_v1, storage

from trainer import refresh_finetuned

# some clients and variables
client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
path_config = json.loads(config_bucket.blob(
    'pathConfig.json').download_as_string())
project_id = path_config['project_id']

# subscribing to refresh requests
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(
    project_id, path_config['sub_trainer_request'])

if __name__ == '__main__':
    import argparse

    from praw_utils import get_reddit

    parser = argparse.ArgumentParser(
        description='search comments by new for user.')
    parser.add_argument('--blocksize', type=int, default=16)
    parser.add_argument('--maxsteps', type=int, default=10)
    parser.add_argument('--forceupdate', type=bool, default=False)
    args = parser.parse_args()

    reddit = get_reddit(client, 'astroturf-dev-configs')

    while True:
        print('Listening')
        response = subscriber.pull(
            request={"subscription": subscription_path, "max_messages": 1})
        for msg in response.received_messages:
            username = msg.message.data.decode('utf-8')
            print(f"Received message: {username}")

        ack_ids = [msg.ack_id for msg in response.received_messages]
        if len(ack_ids) > 0:
            # there's something to do!
            # ack the message first because i don't care about user
            subscriber.acknowledge(
                request={"subscription": subscription_path, "ack_ids": ack_ids})
            # print('ack_ids: {}'.format(ack_ids))
            # run the updates
            print('\nrefresh_finetuned...\n')
            ran = refresh_finetuned(username, blocksize=args.blocksize, maxsteps=args.maxsteps,
                                    force_update=args.forceupdate)
