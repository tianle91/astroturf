import praw
import os
from glob import glob
from google.cloud import storage
from astroturf.infer import (get_qa_string, get_text_generation_pipeline,
                             make_package_infer_url)

client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
model_prefix = 'finetune/dump_finetuned/user/'

def download_models(user_name):
    os.makedirs(model_prefix, exist_ok=True)
    fnames = []
    for blob in client.list_blobs('astroturf-dev-models', prefix=os.path.join(model_prefix, user_name, 'model')):
        if not os.path.isfile(blob.name):
            print('Downloading: {}'.format(blob.name))
            blob.download_to_filename(blob.name)
        fnames.append(blob.name)
    if not len(fnames) > 0:
        raise EnvironmentError('{} has no model files.'.format(user_name))

def clear_models(user_name):
    for fname in glob(os.path.join(model_prefix, user_name, 'model/*')):
        os.remove(fname)

def get_reddit():
    praw_blob = config_bucket.blob('praw.ini')
    praw_blob.download_to_filename(praw_blob.name)
    return praw.Reddit()

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
        download_models(user_name)
    except Exception as e:
        return str(e)
    txtgen = get_text_generation_pipeline(os.path.join(model_prefix, user_name, 'model'))
    reddit = get_reddit()
    package = make_package_infer_url(request_json['url'], reddit)
    prompt = get_qa_string(package)
    responses = txtgen(prompt, max_length=len(prompt.split(' ')) + 128)
    response = responses[0]['generated_text'].replace(prompt, '').strip().split('\n')[0]
    clear_models(user_name)
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
