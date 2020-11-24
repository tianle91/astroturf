import json
import os
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from flask import Flask, flash, redirect, render_template, request, url_for
from google.cloud import pubsub_v1, storage

from main import refresh_local_models, simulate_redditor_response

app = FastAPI()

# some clients and variables
client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')

@app.get("/infer/{username}")
def infer(username: str, url: str):
    return simulate_redditor_response(username, url)

# holy shit this is indeed fast
# uvicorn infer:app --reload
# 127.0.0.1:8000/infer/spez?url=https://www.reddit.com/r/toronto/comments/hkjyjn/city_issues_trespassing_orders_to_demonstrators/fwt4ifw
