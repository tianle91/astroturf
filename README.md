# Astroturf
Gets a particular reddit user's comments, train a model on those comments, then expose model through UI so you can predict what he'd say.

- `users.txt`: Enter interested users here.
- `docker-compose run refreshfinetune`: Get comments for all users in `users.txt`.
- `docker-compose run refreshdata`: Train model for each user in `users.txt`.
- `docker-compose run --service-ports ui`: Start a web UI with available models.

# Infrastructure
```
app: ui -[infer]-> run local inference and serve it
        -[refresh user]-> pub: user_model_update_requests

sub: user_model_update_requests -> {refresh_user_comments, refresh_finetuned}.py 
```
