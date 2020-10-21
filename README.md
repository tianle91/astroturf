# Astroturf
Gets a particular reddit user's comments, train a model on those comments, then expose model through UI so you can predict what he'd say.

# Guide
- `users.txt`: Enter interested users here.
- `docker-compose run getcomments`: Get comments for all users in `users.txt`. Requires `praw.ini` in root folder. More info [here.](https://praw.readthedocs.io/en/latest/getting_started/configuration/prawini.html) Required for training models.
- `docker-compose run finetune`: Train model for each user in `users.txt`. Required for user to be available for querying on UI. You may need a GPU here (refer to `python finetune.py`).
- `docker-compose run --service-ports ui`: Start a web UI with available models in `finetune/{username}/...`.

## Python stuff
To get user comments and train a model on that user...
1. `python data_user_comments.py --users user1 user2 user3`
2. `python finetune.py --users user1 user2 user3`
These users would end up in `finetune/{username}/...` and would be available for inference in the UI. Try smaller `--blocksize` argument if you run out of memory.

## UI
To run the UI, there's a few options depending on what you want to do.
1. docker `docker-compose run --service-ports ui`.
2. debugging `source run_flask.sh`


# Infrastructure
```
app: ui -[inference]-> vm: inference service
        -[refresh user]-> pub/sub: user_update_requests
pub/sub: user_update_requests -> func: scraping service -> pub/sub: training_requests 
pub/sub: training_requests -> vm: training service -> pub/sub: ui_update_requests
```

## Cloud Functions
https://cloud.google.com/sdk/gcloud/reference/functions/deploy

https://github.com/GoogleCloudPlatform/python-docs-samples/tree/master/functions/imagemagick

```
gcloud functions deploy simulate_redditor_reponse \
  --runtime python37 --memory=2048MB --trigger-http --allow-unauthenticated --timeout 60s \
  --service-account storage-admin@astroturf-280818.iam.gserviceaccount.com
```

```
Error: memory limit exceeded. Function invocation was interrupted.

curl --header "Content-Type: application/json" --request POST \
  --data '{"user_name":"spez","password":"https://www.reddit.com/r/toronto/comments/hkjyjn/city_issues_trespassing_orders_to_demonstrators/fwt4ifw"}' \
  https://us-central1-astroturf-280818.cloudfunctions.net/simulate_redditor_reponse
```

