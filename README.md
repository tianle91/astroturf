# Astroturf
To be updated.

## Architecture
<img src="./Architecture.svg">


# Reddit bot
Description
- Responds to “what would u/xxx say”.
- While loop for streaming by new. Submits request for user and link, waits for response.
- Move retrain request into api

Endpoint to-do
- Query for untrained users.
- Query for trained users with option to refresh.
- Waiting for retraining.

Proposal
- Infer endpoint 
  - `GET` returns inference result, with statuses (exists, last updated, cached).
  - `PUT` refreshes local model with new one.
- Trainer endpoint
  - `GET` returns status (exists, last updated, updating). 
    - Subscribes to `[pub/sub]: training_status`.
  - `PUT` allows for request to update model. 
    - Publishes to `[pub/sub]: training_request`.
- Workers 
  - Subscribe to `[pub/sub]: training_request`.
  - Scraper + trainer
  - Publish statuses to `[pub/sub]: training_status` every ? seconds.


# Ops

Updating cloud configs.
`gsutil cp pathConfig.json gs://astroturf-dev-configs/pathConfig.json`
`gsutil cp astroturf-praw.ini gs://astroturf-dev-configs/astroturf-praw.ini`

For testing.
`docker-compose up`

For WSL and GPU.
`docker-compose -f docker-compose-noworker.yml up`
`docker build -t astroturf .`
`docker run -it --gpus=all astroturf python update_worker.py --limit 100 --blocksize 128 --maxsteps 1000 --forceupdate True`
