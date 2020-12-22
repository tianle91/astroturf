import json

from fastapi import FastAPI
from google.cloud import storage

app = FastAPI()

# some clients and variables
client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
path_config = json.loads(config_bucket.blob(
    'pathConfig.json').download_as_string())


@app.get("/{username}")
def status(username: str):
    """some status regarding update of model for username
    """
    pass


@app.put("/{username}")
def update(username: str):
    """publish update request
    """
    pass
