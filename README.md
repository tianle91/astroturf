# astroturf
To get user comments and train a model on that user...
1. `python data_user_comments.py --users user1 user2 user3`
2. `python finetune.py --users user1 user2 user3`

These users would end up in `finetune/{username}/...` and would be available for inference in the UI.

## UI
To run the UI, there's a few options depending on what you want to do.
1. docker `docker-compose run --service-ports ui`.
2. debugging `source run_flask.sh`
