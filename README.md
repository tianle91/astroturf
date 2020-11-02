# Astroturf
Gets a particular reddit user's comments, train a model on those comments, then expose model through UI so you can predict what he'd say.

- `users.txt`: Enter interested users here.
- `docker-compose run refreshfinetune`: Get comments for all users in `users.txt`.
- `docker-compose run refreshdata`: Train model for each user in `users.txt`.
- `docker-compose run --service-ports ui`: Start a web UI with available models.

# Infrastructure
`pub: model_refresh_requests -> sub: model_refresh_servicer`

## UI
- ui allows all users from model bucket to be inferenced always.
- ui downloads user model and runs inference on demand.
- pub: model_refresh_requests. Publishes requests for new model or refresh user model.

## Compute 
- sub: model_refresh_servicer. Scrapes user comments, finetunes model and uploads to model bucket. 
