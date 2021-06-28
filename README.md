# Astroturf
Are you...
- Curious how users might respond to a submission or comment?
- Don't want to wait for a response?
- Want a shitty bot to talk to?

Look no further!

Bot responds to mentions of reddit users in comments.
Currently only monitors [r/AskReddit](https://www.reddit.com/r/AskReddit).

<img src="./bot_screenshot.png" width="1000">


# Architecture
Works locally like so:

<img src="./Architecture.svg" width="400">

## Ops
1. You'll need a `praw.ini`. 
   - Get one [here](https://www.reddit.com/prefs/apps). 
   - By default it looks for `praw.ini` and finds credentials under `[astroturf_bot]`.
2. Build the image. `docker build -t astroturf .`
3. Deploy. `docker-compose up`
