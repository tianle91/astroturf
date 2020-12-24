# Astroturf
Hosted at [http://64.137.143.175](http://64.137.143.175) sometimes (when I'm not gaming).
<img src="./ui_screenshot.png">

## Architecture
<img src="./Architecture.svg">


# Reddit bot (TODO)
Description
- Responds to “what would u/xxx say”.
- While loop for streaming by new. Submits request for user and link, waits for response.
- Move retrain request into api

# Ops

Updating cloud configs.
- `gsutil cp pathConfig.json gs://astroturf-dev-configs/pathConfig.json`
- `gsutil cp astroturf-praw.ini gs://astroturf-dev-configs/astroturf-praw.ini`

Build the image.
`docker build -t astroturf .`

All-in-one.
`docker-compose up`

For WSL and GPU.
- `docker-compose -f docker-compose-noworker.yml up`
- `docker run -it --gpus=all astroturf python update_worker.py --limit 100 --blocksize 128 --maxsteps 1000 --forceupdate True`
