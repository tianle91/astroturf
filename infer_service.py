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

cached_txtgen = {}
cached_max_count = 10


@app.get("/{username}")
def infer(username: str, url: str = defaulturl, refresh: bool = False):
    if refresh or username not in cached_txtgen:
        local_model_path_user = get_local_models(username, force_update=True)
        txtgen = get_text_generation_pipeline(local_model_path_user)
        cached_txtgen[username] = (txtgen, 1)
        if len(cached_txtgen.keys()) > cached_max_count:
            # pop the least used key
            min_n = min(v[1] for _, v in cached_txtgen.items())
            for k, n in cached_txtgen:
                if n == min_n:
                    cached_txtgen.pop(k)
    else:
        txtgen, n = cached_txtgen[username]
        cached_txtgen[username] = (txtgen, n+1)
    response = simulate_pipeline_response(txtgen, url)
    print(cached_txtgen)
    return response
