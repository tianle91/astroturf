import os
from glob import glob
from google.cloud import storage
from astroturf.finetune import dump_finetuned

def refresh_finetuned(
    user_name,
    blocksize=16,
    max_steps=10,
    force_update=False,
    data_bucket='astroturf-dev-data',
    data_prefix='prawtools/make_package_training/user/',
    model_bucket='astroturf-dev-models',
    model_prefix='finetune/dump_finetuned/user/',
):
    client = storage.Client()
    data_prefix_user = os.path.join(data_prefix, user_name)
    os.makedirs(data_prefix_user, exist_ok=True)

    model_prefix_user = os.path.join(model_prefix, user_name)
    bucket = client.bucket(model_bucket)
    output_flags = [os.path.join(model_prefix_user, 'model/{}'.format(s)) for s in [
        'pytorch_model.bin', 'config.json', 'training_args.bin'
    ]]
    if not force_update and all(bucket.blob(s).exists() for s in output_flags):
        print ('Skip refresh_finetuned due to existing output_flags:\n{}'.format('\n'.join(output_flags)))
        return False

    # download files for training
    for blob in client.list_blobs(data_bucket, prefix=data_prefix_user):
        if not os.path.isfile(blob.name):
            print ('Downloading: {}'.format(blob.name))
            blob.download_to_filename(blob.name)

    dump_finetuned(data_prefix_user, model_prefix_user, blocksize, max_steps)
    for fname in glob(os.path.join(model_prefix_user, 'model/*')):
        print ('Uploading: {}'.format(fname))
        blob = bucket.blob(fname)
        blob.upload_from_filename(fname)
    return True

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='finetune on user comments.')
    parser.add_argument('--users', type=str, nargs='*')
    parser.add_argument('--blocksize', type=int, default=16)
    args = parser.parse_args()

    # list of users
    if args.users is None:
        with open('users.txt') as f:
            users = f.read().split()
    else:
        users = list(args.users)

    for user_name in users:
        print('user_name: {} running...'.format(user_name))
        ran = refresh_finetuned(user_name, blocksize=args.blocksize)
