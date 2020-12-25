import json

from fastapi import FastAPI
from google.cloud import storage
from transformers import pipeline

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


def get_txtgen_cached_or_otherwise(username, force_update=False) -> pipeline:
    """Gets model and updates cache with it.
    """
    global cached_txtgen

    if username in cached_txtgen and not force_update:
        txtgen, n = cached_txtgen[username]
        cached_txtgen[username] = (txtgen, n+1)
        return txtgen

    # otherwise, need to load
    local_model_path_user = get_local_models(
        username, force_update=force_update)
    txtgen = get_text_generation_pipeline(local_model_path_user)

    # drop least used model in cached_txtgen if required
    if len(cached_txtgen.keys()) > cached_max_count:
        min_count = min(cached_txtgen[u][1] for u in cached_txtgen)
        # will drop first min_count username
        to_drop_username = None
        for u in cached_txtgen:
            if cached_txtgen[u][1] == min_count:
                to_drop_username = u
                break
        print(f'Evicting {to_drop_username} from cached_txtgen.')
        cached_txtgen = {
            u: (v[0], v[1]-min_count)
            for u, v in cached_txtgen.items() if u != to_drop_username
        }

    # add txtgen to cached_txtgen
    new_count = 1
    if username in cached_txtgen:
        new_count = cached_txtgen[username][1] + 1
    cached_txtgen[username] = (txtgen, new_count)

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
