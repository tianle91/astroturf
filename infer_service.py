import json

from fastapi import FastAPI
from google.cloud import storage

from infer import (get_local_models, get_text_generation_pipeline,
                   simulate_pipeline_response)

app = FastAPI()

# some clients and variables
client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
path_config = json.loads(config_bucket.blob(
    'pathConfig.json').download_as_string())
defaulturl = path_config['defaulturl']

cached_txtgen = {}  # {text_generation_pipeline: count of calls}
cached_max_count = 10


def get_txtgen_cached_or_otherwise(username, force_update=False):
    """Gets model and updates cache with it.
    """
    if username in cached_txtgen:
        txtgen, n = cached_txtgen[username]
        cached_txtgen[username] = (txtgen, n+1)
    else:
        local_model_path_user = get_local_models(
            username, force_update=force_update)
        txtgen = get_text_generation_pipeline(local_model_path_user)
        cached_txtgen[username] = (txtgen, 1)
        if len(cached_txtgen.keys()) > cached_max_count:
            # pop the least used key
            min_n = min(v[1] for _, v in cached_txtgen.items())
            for username_temp in cached_txtgen:
                _, count_temp = cached_txtgen[username_temp]
                if count_temp == min_n:
                    cached_txtgen.pop(username_temp)
    return txtgen


@app.get("/infer/{username}")
def infer(username: str, url: str = defaulturl):
    txtgen = get_txtgen_cached_or_otherwise(username)
    response = simulate_pipeline_response(txtgen, url)
    print(cached_txtgen)
    return response


@app.get("/refresh/{username}")
def refresh(username: str):
    if username in cached_txtgen:
        cached_txtgen.pop(username)
    get_txtgen_cached_or_otherwise(username, force_update=True)
    return True
