# Astroturf
To be updated.

## Architecture
<img src="./Architecture.svg">



## Ops

`gsutil cp pathConfig.json gs://astroturf-dev-configs/pathConfig.json`

`export imagepath=gcr.io/astroturf-280818/astroturf_infer && docker build -f Dockerfile.infer -t $imagepath . && docker push $imagepath`
