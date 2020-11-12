import json
import os
from datetime import datetime
from typing import List
from typing import Optional

from google.cloud import storage
from google.cloud.storage import Blob
from praw import Reddit
from prawcore.exceptions import NotFound

from praw_utils import get_reddit
from statusflags import StatusFlags

client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
path_config = json.loads(config_bucket.blob('pathConfig.json').download_as_string())
model_bucket = client.bucket(path_config['model_bucket'])
status_bucket = client.bucket(path_config['status_bucket'])

# some local variables
local_model_path = '/tmp/models/'
reddit = get_reddit(client, 'astroturf-dev-configs')


def get_reloaded_if_exists(blob: Blob) -> Blob:
    if blob.exists():
        blob.reload()
    return blob


def status(username: str) -> str:
    data_refresh_success = get_reloaded_if_exists(status_bucket.blob(
        os.path.join(username, StatusFlags.data_refresh_success)
    ))
    data_refresh_progress = get_reloaded_if_exists(status_bucket.blob(
        os.path.join(username, StatusFlags.data_refresh_progress)
    ))
    model_training_progress = get_reloaded_if_exists(status_bucket.blob(
        os.path.join(username, StatusFlags.model_training_progress)
    ))
    model_training_success = get_reloaded_if_exists(status_bucket.blob(
        os.path.join(username, StatusFlags.model_training_success)
    ))
    return '\n'.join([
        'data_refresh_progress: updated: {}'.format(data_refresh_progress.updated),
        'data_refresh_success: updated: {}'.format(data_refresh_success.updated),
        'model_training_progress: updated: {}'.format(model_training_progress.updated),
        'model_training_success: updated: {}'.format(model_training_success.updated),
    ])


def get_trained_usernames() -> List[str]:
    resl = []
    for blob in client.list_blobs(status_bucket, prefix=''):
        name_split = blob.name.split('/')
        user_name = name_split[0]
        if len(name_split) > 1:
            fname = name_split[1]
            if fname == StatusFlags.model_training_success:
                resl.append(user_name)
    return resl


def last_trained(username: str) -> Optional[datetime]:
    return get_reloaded_if_exists(status_bucket.blob(
        os.path.join(username, StatusFlags.model_training_success)
    )).updated


def last_refreshed(username: str) -> Optional[datetime]:
    return get_reloaded_if_exists(status_bucket.blob(
        os.path.join(username, StatusFlags.data_refresh_success)
    )).updated


def is_invalid(username: str, r: Reddit) -> bool:
    if len(username) == 0:
        # not catched by NotFound (as of 2020-11-04)
        return True
    try:
        r.redditor(name=username).id
    except NotFound:
        return True
    return False
