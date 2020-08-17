# Astroturf
Gets a particular reddit user's comments, train a model on those comments, then expose model through UI so you can predict what he'd say.

# Guide
- `users.txt`: Enter interested users here.
- `docker-compose run getcomments`: Get comments for all users in `users.txt`. Requires `praw.ini` in root folder. More info [here.](https://praw.readthedocs.io/en/latest/getting_started/configuration/prawini.html) Required for training models.
- `docker-compose run finetune`: Train model for each user in `users.txt`. Required for user to be available for querying on UI.
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
