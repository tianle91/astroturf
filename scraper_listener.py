import json

from google.cloud import pubsub_v1
from google.cloud import storage

from scraper import refresh_user_comments


# some clients and variables
client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
path_config = json.loads(config_bucket.blob(
    'pathConfig.json').download_as_string())
project_id = path_config['project_id']

# subscribing to scraper requests
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(
    project_id, path_config['sub_scraper_request'])

# publishing to trainer requests
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(
    project_id, path_config['pub_trainer_request'])

if __name__ == '__main__':
    import argparse
    from praw_utils import get_reddit

    parser = argparse.ArgumentParser(
        description='search comments by new for user.')
    parser.add_argument('--limit', type=int, default=100)
    args = parser.parse_args()

    reddit = get_reddit(client, 'astroturf-dev-configs')

    while True:
        print('Listening')
        response = subscriber.pull(
            request={"subscription": subscription_path, "max_messages": 1})
        for msg in response.received_messages:
            user_name = msg.message.data.decode('utf-8')
            print("Received message:", user_name)

        ack_ids = [msg.ack_id for msg in response.received_messages]
        if len(ack_ids) > 0:
            # there's something to do!
            # ack the message first because i don't care about user
            subscriber.acknowledge(
                request={"subscription": subscription_path, "ack_ids": ack_ids})
            # print('ack_ids: {}'.format(ack_ids))
            # run the updates
            print('\nrefresh_user_comments...\n')
            status = refresh_user_comments(user_name, reddit, limit=args.limit)

            future = publisher.publish(topic_path, str.encode(username))
            message_id = future.result()
            print(f'\npublished trainer request, id: {message_id}\n')