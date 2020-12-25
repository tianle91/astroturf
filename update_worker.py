import json

from google.cloud import pubsub_v1, storage

from scraper import refresh_user_comments_cloud
from trainer import refresh_finetuned_cloud

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
topic_path = publisher.topic_path(
    project_id, path_config['pub_update_status'])


def get_future_from_publish_status_message(username, status):
    return publisher.publish(
        topic_path,
        data=str.encode(username),
        status=str.encode(status)
    )


if __name__ == '__main__':
    import argparse

    from praw_utils import get_reddit

    parser = argparse.ArgumentParser(
        description='search comments by new for user.')
    parser.add_argument('--limit', type=int, default=100)
    parser.add_argument('--blocksize', type=int, default=256)
    parser.add_argument('--maxsteps', type=int, default=500)
    parser.add_argument('--forceupdate', type=bool, default=True)
    parser.add_argument('--site', type=str, default='astroturf_bot')
    args = parser.parse_args()

    reddit = get_reddit(client, 'astroturf-dev-configs', site=args.site)

    while True:
        print('Listening')
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
                username, status='received_request'))
            # there's something to do! ack it to remove from queue.
            subscriber.acknowledge(
                request={"subscription": subscription_path, "ack_ids": ack_ids})
            # update comments
            refreshed_comment_ids = refresh_user_comments_cloud(
                username, reddit, limit=args.limit)
            pub_futures.append(get_future_from_publish_status_message(
                username, status='refresh_user_comments_cloud'))
            if len(refreshed_comment_ids) > 0:
                # update finetuned
                username_finedtuned = refresh_finetuned_cloud(
                    username,
                    blocksize=args.blocksize,
                    maxsteps=args.maxsteps,
                    force_update=args.forceupdate
                )
                pub_futures.append(get_future_from_publish_status_message(
                    username, status='refresh_finetuned_cloud'))
            else:
                pub_futures.append(get_future_from_publish_status_message(
                    username, status='no_new_comments'))
            # done!
            pub_futures.append(get_future_from_publish_status_message(
                username, status='success'))

        message_ids = [f.result() for f in pub_futures]
        if len(message_ids) > 0:
            print(message_ids)
