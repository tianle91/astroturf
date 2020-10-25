import configparser
import json
import os

import flask
import praw
from google.cloud import storage

from astroturf.finetune import model_output_fnames
from astroturf.infer import (get_qa_string, get_text_generation_pipeline,
                             make_package_infer_url)
from gcp_utils import download_all_cloud_files_with_prefix

client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
path_config = json.loads(config_bucket.blob('pathConfig.json').download_as_string())
model_bucket = path_config['model_bucket']
cloud_model_path = path_config['model_path']
local_model_path = '/tmp/models/'

def refresh_local_models(user_name, force_update=False):
    """return local path for model files for user==user_name"""
    cloud_model_path_user = os.path.join(cloud_model_path, user_name, 'model')
    local_model_path_user = os.path.join(local_model_path, user_name, 'model')
    # skip refresh
    targets_exist = [os.path.isfile(os.path.join(local_model_path_user, fname)) for fname in model_output_fnames]
    if not force_update and all(targets_exist):
        return local_model_path_user
    # refresh
    downloaded_fnames = download_all_cloud_files_with_prefix(
        local_model_path_user, model_bucket, cloud_model_path_user, client
    )
    if not len(downloaded_fnames) > 0:
        raise ValueError('{} has no model files.'.format(user_name))
    return local_model_path_user

def get_reddit():
    praw_blob = config_bucket.blob('praw.ini')
    config = configparser.ConfigParser()
    config.read_string(praw_blob.download_as_text())
    return praw.Reddit(**config['DEFAULT'])

def simulate_redditor_reponse(request: flask.Request):
    """HTTP Cloud Function. Returns response text or any valid input to
    https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response
    """
    request_json = request.get_json(silent=True)
    user_name = request_json['user_name']
    try:
        local_model_path_user = refresh_local_models(user_name)
    except Exception as e:
        return str(e)
    reddit = get_reddit()
    txtgen = get_text_generation_pipeline(local_model_path_user)
    package = make_package_infer_url(request_json['url'], reddit)
    prompt = get_qa_string(package)
    responses = txtgen(prompt, max_length=len(prompt.split(' ')) + 128)
    response = responses[0]['generated_text'].replace(prompt, '').strip().split('\n')[0]
    request_json.update({
        'prompt': prompt,
        'response': response
    })
    return request_json


if __name__ == '__main__':
    class DummyRequest:
        def get_json(self, *args, **kwargs):
            return {
                "user_name":"spez",
                "url":"https://www.reddit.com/r/toronto/comments/hkjyjn/city_issues_trespassing_orders_to_demonstrators/fwt4ifw"
            }
    print (simulate_redditor_reponse(DummyRequest()))
