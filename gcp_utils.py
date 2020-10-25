import os
from glob import glob

from google.cloud import storage


def upload_all_local_files_with_prefix(
    local_prefix: str,
    cloud_bucket: str, cloud_prefix: str,
    client: storage.Client
):
    bucket = client.bucket(cloud_bucket)
    fnames = []
    for local_path_temp in glob(os.path.join(local_prefix, '*')):
        fname = local_path_temp.split('/')[-1]
        print ('Uploading: {fname} to bucket: {bkt} at prefix: {prfx}'.format(
            fname=fname,
            bkt=cloud_bucket,
            prfx=cloud_prefix
        ))
        blob = bucket.blob(os.path.join(cloud_prefix, fname))
        blob.upload_from_filename(local_path_temp)
        fnames.append(fname)
    return fnames

def download_all_cloud_files_with_prefix(
    local_prefix: str,
    cloud_bucket: str, cloud_prefix: str,
    client: storage.Client,
    refresh_local: bool = True
):
    os.makedirs(local_prefix, exist_ok=True)
    fnames = []
    for blob in client.list_blobs(cloud_bucket, prefix=cloud_prefix):
        fname = blob.name.split('/')[-1]
        local_path = os.path.join(local_prefix, fname)
        if not os.path.isfile(local_path) or refresh_local:
            print('Downloading: {fname} to local prefix: {prfx}'.format(
                fname=fname,
                prfx=local_prefix
            ))
            blob.download_to_filename(local_path)
        fnames.append(fname)
    return fnames