import json

from google.cloud import pubsub_v1, storage

from scraper import refresh_user_comments_cloud
from status import get_trained_usernames

# some clients and variables
client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
path_config = json.loads(config_bucket.blob(
    'pathConfig.json').download_as_string())
project_id = path_config['project_id']

# subscribing to sub_update_request
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(
    project_id, path_config['sub_update_request'])

# publishing to pub_update_status
publisher = pubsub_v1.PublisherClient()
topic_path_status = publisher.topic_path(
    project_id, path_config['pub_update_status'])

# publishing to pub_train_request
publisher = pubsub_v1.PublisherClient()
topic_path_train = publisher.topic_path(
    project_id, path_config['pub_train_request'])


def get_future_from_publish_status_message(username, status, topic_path):
    return publisher.publish(
        topic_path,
        data=str.encode(username),
        status=str.encode(status)
    )


if __name__ == '__main__':
    import argparse

    from praw_utils import get_reddit

    parser = argparse.ArgumentParser(
        description='update for user.')
    parser.add_argument('--limit', type=int, default=500)
    parser.add_argument('--site', type=str, default='astroturf_bot')
    args = parser.parse_args()

    reddit = get_reddit(client, 'astroturf-dev-configs', site=args.site)

    print('Ready')
    while True:
        response = subscriber.pull(
            request={"subscription": subscription_path, "max_messages": 1})

        username = None
        ack_ids = []
        for msg in response.received_messages:
            username = msg.message.data.decode('utf-8')
            print(f"Received message: {username}")
            ack_ids.append(msg.ack_id)

        pub_futures = []
        if len(ack_ids) > 0 and username is not None:
            pub_futures.append(get_future_from_publish_status_message(
                username, 
                status='received update request', 
                topic_path=topic_path_status
            ))
            # there's something to do! ack it to remove from queue.
            subscriber.acknowledge(
                request={"subscription": subscription_path, "ack_ids": ack_ids})
            # update comments
            refreshed_comment_ids = refresh_user_comments_cloud(
                username, reddit, limit=args.limit)
            pub_futures.append(get_future_from_publish_status_message(
                username, 
                status='refresh comments success',
                topic_path=topic_path_status
            ))
            if len(refreshed_comment_ids) > 0 or not username in get_trained_usernames():
                pub_futures.append(get_future_from_publish_status_message(
                    username, 
                    status='', 
                    topic_path=topic_path_train
                ))
                pub_futures.append(get_future_from_publish_status_message(
                    username, 
                    status='submitted train request', 
                    topic_path=topic_path_status
                ))
            else:
                pub_futures.append(get_future_from_publish_status_message(
                    username, 
                    status='no new comments', 
                    topic_path=topic_path_status
                ))

        message_ids = [f.result() for f in pub_futures]
        if len(message_ids) > 0:
            print(message_ids)
