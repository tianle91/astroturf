# Astroturf
To be updated.

## Architecture
<img src="./Architecture.svg">


## Ops

`gsutil cp pathConfig.json gs://astroturf-dev-configs/pathConfig.json`
`gsutil cp astroturf-praw.ini gs://astroturf-dev-configs/astroturf-praw.ini`

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
- Trainer endpoint
  - Workers subscribe to update pub/sub.
    - Scraper + trainer
    - Publish updates and statuses every X seconds.
  - `GET` returns status (exists, last updated, updating).
  - `PUT` allows for request to update model. Publishes.
- Infer endpoint 
  - `GET` returns inference result, with statuses (exists, last updated, cached).
  - `PUT` refreshes local model with new one.
