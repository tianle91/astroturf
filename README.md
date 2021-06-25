# Astroturf
Are you...
- Curious how users might respond to a submission or comment?
- Don't want to wait for a response?
- Want a shitty bot to talk to?

Look no further!

Bot responds to “what would u/xxx say” or something similar. Currently only monitors [r/AskReddit](https://www.reddit.com/r/AskReddit).

<img src="./bot_screenshot.png" width="300">


# Architecture
Ok so mostly this is how it works.

<img src="./Architecture.svg" width="500">

## Ops
1. You'll need a `praw.ini`.
2. Build the image. `docker build -t astroturf .`
3. Deploy. `docker-compose up`
