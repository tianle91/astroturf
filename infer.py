import json
import os
from typing import Dict

from google.cloud import storage
from transformers import pipeline

from astroturf.finetune import get_qa_string
from astroturf.infer import (get_text_generation_pipeline,
                             make_package_infer_url)
from gcp_utils import download_all_cloud_files_with_prefix
from praw_utils import get_reddit

client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
path_config = json.loads(config_bucket.blob(
    'pathConfig.json').download_as_string())
model_bucket = client.bucket(path_config['model_bucket'])

# some local variables
local_model_path = '/tmp/astroturf/models/'
reddit = get_reddit(client, 'astroturf-dev-configs')


def get_local_models(username, force_update=False):
    """return local path for model files for user==user_name"""
    local_model_path_user = os.path.join(local_model_path, username, 'model')
    if not os.path.isdir(local_model_path_user) or force_update:
        cloud_model_path_user = os.path.join(username, 'model')
        fnames = download_all_cloud_files_with_prefix(
            local_model_path_user, model_bucket.name, cloud_model_path_user, client,
            refresh_local=force_update
        )
        if not len(fnames) > 0:
            raise ValueError('{} has no model files.'.format(username))
    return local_model_path_user


def simulate_pipeline_response(pipeline: pipeline, url: str) -> Dict[str, str]:
    package = make_package_infer_url(url, reddit)
    prompt = get_qa_string(package)
    responses = pipeline(prompt, max_length=len(prompt.split(' ')) + 128)
    return {
        'prompt': prompt,
        # .split('\n')[0]
        'response': responses[0]['generated_text'].replace(prompt, '').strip()
    }


def simulate_redditor_response(username, url, force_update: bool = False):
    try:
        local_model_path_user = get_local_models(
            username, force_update=force_update)
    except Exception as e:
        return str(e)
    return simulate_pipeline_response(
        get_text_generation_pipeline(local_model_path_user),
        url=url
    )


if __name__ == '__main__':
    username = 'spez'
    url = 'https://www.reddit.com/r/toronto/comments/hkjyjn/city_issues_trespassing_orders_to_demonstrators/fwt4ifw'
    print(simulate_redditor_response(username, url))
