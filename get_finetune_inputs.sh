mkdir data
mkdir data/user
gsutil -m rsync -r gs://astroturf-dev/data/user data/user 