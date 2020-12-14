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
- Merge scraper and trainer together, put behind a new trainer endpoint.
  - `GET` returns some info regarding status such as exists or not, last updated, updating, etc.
  - `PUT` allows for request to update model.
- Infer endpoint has resource not available as response to a `GET`.
- Deprecate status flags in ui in favour of getting info from Trainer/Infer endpoint.
  - No more progress updates through flags in bucket (status bucket will be deprecated).
  - Only model last update time using blob attributes.
