# Astroturf
Gets a particular reddit user's comments, train a model on those comments, then expose model through UI so you can predict what he'd say.

# Guide
- `users.txt`: Enter interested users here.
- `docker-compose run getcomments`: Get comments for all users in `users.txt`.
- `docker-compose run finetune`: Train model for each user in `users.txt`.
- `docker-compose run --service-ports ui`: Start a web UI with available models.

## Python stuff
To get user comments and train a model on that user...
1. `python data_user_comments.py --users user1 user2 user3`
2. `python finetune.py --users user1 user2 user3`

## UI
To run the UI, there's a few options depending on what you want to do.
1. docker `docker-compose run --service-ports ui`.


# Infrastructure
```
app: ui -[infer]-> run local inference and serve it
        -[refresh user]-> pub: user_model_update_requests

sub: user_model_update_requests -> {refresh_user_comments, refresh_finetuned}.py 
```
