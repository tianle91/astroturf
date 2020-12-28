import json

from google.cloud import pubsub_v1, storage

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
    project_id, path_config['sub_train_request'])

# publishing to pub_update_status
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(
    project_id, path_config['pub_update_status'])


def get_future_from_publish_status_message(username, status, topic_path):
    return publisher.publish(
        topic_path,
        data=str.encode(username),
        status=str.encode(status)
    )


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='train for user.')
    parser.add_argument('--blocksize', type=int, default=256)
    parser.add_argument('--maxsteps', type=int, default=500)
    parser.add_argument('--forceupdate', type=bool, default=True)
    args = parser.parse_args()

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
                username, status='received train request', topic_path=topic_path))
            # there's something to do! ack it to remove from queue.
            subscriber.acknowledge(
                request={"subscription": subscription_path, "ack_ids": ack_ids})
            username_finedtuned = refresh_finetuned_cloud(
                username,
                blocksize=args.blocksize,
                maxsteps=args.maxsteps,
                force_update=args.forceupdate
            )
            pub_futures.append(get_future_from_publish_status_message(
                username, status='train success', topic_path=topic_path))

        message_ids = [f.result() for f in pub_futures]
        if len(message_ids) > 0:
            print(message_ids)
