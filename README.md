# Astroturf
Curious how users might respond to a submission or comment? Me too.
- Hosted at [http://64.137.143.175](http://64.137.143.175) sometimes (when I'm not gaming).
- Bot responds to “what would u/xxx say” or something similar. Currently only monitors [r/AskReddit](https://www.reddit.com/r/AskReddit).

## Screenshots
Check out the amazing and insightful responses!

### UI
<img src="./ui_screenshot.png" width="400">

### Bot
<img src="./bot_screenshot.png" width="300">

## Architecture
Ok so mostly this is how it works.
<img src="./Architecture.svg" width="500">


# Ops
This project is developed on GCP and relies on Storage and Pub/Sub.

Compute is local and runs on a 8-core device, 64Gb ram and a GTX 1080 Ti.
Runs on top of Windows 10 (dev build), WSL2, Nvidia for WSL and Docker Desktop.

1. Build the image. `docker build -t astroturf .`
2. Deployment
	- All-in-one (testing only). `docker-compose up`
	- For WSL and GPU. https://www.docker.com/blog/wsl-2-gpu-support-is-here/
		- `docker-compose -f docker-compose-noworker.yml up`
		- `docker run -it --gpus=all astroturf python -u update_worker.py --site astroturf_update_worker`

## Updating configs
Some configs are stored in a bucket.
- `gsutil cp pathConfig.json gs://astroturf-dev-configs/pathConfig.json`
- `gsutil cp astroturf-praw.ini gs://astroturf-dev-configs/astroturf-praw.ini`
