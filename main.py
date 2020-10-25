import configparser
import os
from glob import glob

import praw
from google.cloud import storage

from astroturf.infer import (get_qa_string, get_text_generation_pipeline,
                             make_package_infer_url)

client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
model_prefix = 'finetune/dump_finetuned/user/'
local_model_path = '/tmp/model/'

def refresh_models(user_name, force_update=False):
    os.makedirs(local_model_path, exist_ok=True)
    prefix = os.path.join(model_prefix, user_name, 'model')
    # skip refresh
    if not force_update and os.path.isfile(os.path.join(prefix, 'pytorch_model.bin')):
        return True
    # refresh
    fnames = []
    for blob in client.list_blobs('astroturf-dev-models', prefix=prefix):
        if not os.path.isfile(blob.name):
            localpathtemp = os.path.join(local_model_path, blob.name.split('/')[-1])
            print('Downloading: {} to {}'.format(blob.name, localpathtemp))
            blob.download_to_filename(localpathtemp)
        fnames.append(blob.name)
    if not len(fnames) > 0:
        raise EnvironmentError('{} has no model files.'.format(user_name))
    return True

def clear_models():
    for fname in glob(os.path.join(local_model_path, '*')):
        os.remove(fname)

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
        refresh_models(user_name)
    except Exception as e:
        return str(e)
    reddit = get_reddit()
    txtgen = get_text_generation_pipeline(local_model_path)
    package = make_package_infer_url(request_json['url'], reddit)
    prompt = get_qa_string(package)
    responses = txtgen(prompt, max_length=len(prompt.split(' ')) + 128)
    response = responses[0]['generated_text'].replace(prompt, '').strip().split('\n')[0]
    clear_models()
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
