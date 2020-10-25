import configparser
import json
import os

import praw
from google.cloud import storage

from astroturf.infer import (get_qa_string, get_text_generation_pipeline,
                             make_package_infer_url)

client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
path_config = json.loads(config_bucket.blob('pathConfig.json').download_as_string())
model_bucket = path_config['model_bucket']
cloud_model_path = path_config['model_path']
local_model_path = '/tmp/models/'

def refresh_local_models(user_name, force_update=False):
    """return local path for model files for user==user_name"""
    cloud_model_path_user = os.path.join(cloud_model_path, user_name, 'model')
    local_model_path_user = os.path.join(local_model_path, user_name)
    os.makedirs(local_model_path_user, exist_ok=True)
    # skip refresh
    if not force_update and os.path.isfile(os.path.join(local_model_path_user, 'pytorch_model.bin')):
        print('pytorch_model.bin exists! skipping refresh.')
        return local_model_path_user
    # refresh
    fnames = []
    for blob in client.list_blobs(model_bucket, prefix=cloud_model_path_user):
        if force_update or not os.path.isfile(blob.name):
            fname = blob.name.split('/')[-1]
            local_path_temp = os.path.join(local_model_path_user, fname)
            print('Downloading: {} to {}'.format(blob.name, local_path_temp))
            blob.download_to_filename(local_path_temp)
        fnames.append(blob.name)
    if not len(fnames) > 0:
        raise EnvironmentError('{} has no model files.'.format(user_name))
    return local_model_path_user

def get_reddit():
    praw_blob = config_bucket.blob('praw.ini')
    config = configparser.ConfigParser()
    config.read_string(praw_blob.download_as_text())
    return praw.Reddit(**config['DEFAULT'])

def simulate_redditor_reponse(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
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
