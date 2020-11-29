import json
import os
from datetime import datetime, timezone
from typing import List, Optional

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


def get_compact_timedelta_str_from_seconds(seconds: int) -> str:
    s = seconds
    if s < 60:
        return f'{s}s ago'
    m = s // 60
    if m < 60:
        return f'{m}m ago'
    h = m // 60
    if h < 60:
        return f'{h}h ago'
    d = h // 24
    if d < 60:
        return f'{d}d ago'
    return '>60d ago'


def get_compact_time_since(dt: Optional[datetime]) -> str:
    utcnow = datetime.now(timezone.utc)
    if dt is None:
        return '?'
    return get_compact_timedelta_str_from_seconds((utcnow - dt).seconds)

def status(username: str) -> str:
    refresh_request = get_reloaded_if_exists(status_bucket.blob(
        os.path.join(username, StatusFlags.refresh_request)
    ))
    # data refresh
    data_refresh_success = get_reloaded_if_exists(status_bucket.blob(
        os.path.join(username, StatusFlags.data_refresh_success)
    ))
    data_refresh_progress = get_reloaded_if_exists(status_bucket.blob(
        os.path.join(username, StatusFlags.data_refresh_progress)
    ))
    data_refresh_progress_str = ''
    if data_refresh_progress.exists():
        data_refresh_progress_str = data_refresh_progress.download_as_string().decode("utf-8")
    # model training
    model_training_progress = get_reloaded_if_exists(status_bucket.blob(
        os.path.join(username, StatusFlags.model_training_progress)
    ))
    model_training_success = get_reloaded_if_exists(status_bucket.blob(
        os.path.join(username, StatusFlags.model_training_success)
    ))
    n = len('>60 days ago')
    return '\n'.join([
        'refresh_request:         {}'.format(
            get_compact_time_since(refresh_request.updated).rjust(n)
        ),
        'data_refresh_progress:   {} {}'.format(
            get_compact_time_since(data_refresh_progress.updated).rjust(n),
            data_refresh_progress_str
        ),
        'data_refresh_success:    {}'.format(
            get_compact_time_since(data_refresh_success.updated).rjust(n)
        ),
        'model_training_progress: {}'.format(
            get_compact_time_since(model_training_progress.updated).rjust(n)
        ),
        'model_training_success:  {}'.format(
            get_compact_time_since(model_training_success.updated).rjust(n)
        ),
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


def last_request(username: str) -> Optional[datetime]:
    return get_reloaded_if_exists(status_bucket.blob(
        os.path.join(username, StatusFlags.refresh_request)
    )).updated


def last_success(username: str) -> Optional[datetime]:
    return get_reloaded_if_exists(status_bucket.blob(
        os.path.join(username, StatusFlags.model_training_success)
    )).updated


def last_progress(username: str) -> Optional[datetime]:
    data_refresh_progress_updated = get_reloaded_if_exists(status_bucket.blob(
        os.path.join(username, StatusFlags.data_refresh_progress)
    )).updated
    model_training_progress_updated = get_reloaded_if_exists(status_bucket.blob(
        os.path.join(username, StatusFlags.model_training_progress)
    )).updated
    progresses = [data_refresh_progress_updated, model_training_progress_updated]
    progresses = [dt for dt in progresses if dt is not None]
    return None if len(progresses) == 0 else max(progresses)


def is_invalid(username: str, r: Reddit) -> bool:
    if len(username) == 0:
        # not catched by NotFound (as of 2020-11-04)
        return True
    try:
        r.redditor(name=username).id
    except NotFound:
        return True
    return False
