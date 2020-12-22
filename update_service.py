import json

import pandas as pd
from fastapi import FastAPI
from google.api_core.exceptions import DeadlineExceeded
from google.cloud import pubsub_v1, storage

app = FastAPI()

# some clients and variables
client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
path_config = json.loads(config_bucket.blob(
    'pathConfig.json').download_as_string())
project_id = path_config['project_id']

# subscribing to sub_update_status
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(
    project_id, path_config['sub_update_status'])

# publishing to pub_update_request
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(
    project_id, path_config['pub_update_request'])

status_df = pd.DataFrame({'username': [], 'dt': [], 'status': []})


def get_last_status_dt_per_user(status_df: pd.DataFrame) -> pd.DataFrame:
    resl = []
    for index, subdf in status_df.groupby(['username', 'status']):
        username, status = index
        resl.append({
            'username': username,
            'dt': max(subdf['dt']),
            'status': status
        })
    return pd.DataFrame(status_df)


def get_new_statuses() -> pd.DataFrame:
    resl = []
    try:
        response = subscriber.pull(
            request={"subscription": subscription_path, "max_messages": 100}, timeout=1)
    except DeadlineExceeded:
        return pd.DataFrame(resl)
    ack_ids = []
    for msg in response.received_messages:
        resl.append({
            'username': msg.message.data.decode('utf-8'),
            'dt': msg.message.publish_time,
            'status': msg.message.attributes['status']
        })
        ack_ids.append(msg.ack_id)
    if len(ack_ids) > 0:
        subscriber.acknowledge(
            request={"subscription": subscription_path, "ack_ids": ack_ids})
    return pd.DataFrame(resl)


@app.get("/status/{username}")
def status(username: str):
    """some status regarding update of model for username
    """
    global status_df
    new_statuses = get_new_statuses()
    if len(new_statuses) > 0:
        status_df = status_df.append(new_statuses, ignore_index=True)
        status_df = get_last_status_dt_per_user(status_df)
    if username in status_df['username'].values:
        return {
            row['status']: row['dt']
            for _, row in status_df[status_df['username'] == username].iterrows()
        }


@app.get("/update/{username}")
def update(username: str):
    """publish update request
    """
    future = publisher.publish(topic_path, data=str.encode(username))
    message_id = future.result()
    return message_id
