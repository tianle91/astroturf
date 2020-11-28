import json
import os

from google.cloud import storage

from astroturf.finetune import dump_finetuned, model_output_fnames
from gcp_utils import (download_all_cloud_files_with_prefix,
                       upload_all_local_files_with_prefix)
from statusflags import StatusFlags

client = storage.Client()
config_bucket = client.bucket('astroturf-dev-configs')
path_config = json.loads(config_bucket.blob('pathConfig.json').download_as_string())
data_bucket = client.bucket(path_config['data_bucket'])
model_bucket = client.bucket(path_config['model_bucket'])
status_bucket = client.bucket(path_config['status_bucket'])

# some local variables
local_data_path = 'data'
local_model_path = 'models'


def refresh_finetuned(
        user_name,
        blocksize=16,
        maxsteps=10,
        force_update=False
) -> str:
    # set up local directories
    local_model_path_user = os.path.join(local_model_path, user_name)
    local_data_path_user = os.path.join(local_data_path, user_name)
    os.makedirs(local_model_path_user, exist_ok=True)
    os.makedirs(local_data_path_user, exist_ok=True)

    # progress status tracker
    status_progress = status_bucket.blob(os.path.join(user_name, StatusFlags.model_training_progress))
    status_progress.upload_from_string('starting')

    # set up some output flags for completion check
    output_flags = [os.path.join(user_name, s) for s in model_output_fnames]

    # skip if not force_update and model exists
    if not force_update and all(model_bucket.blob(s).exists() for s in output_flags):
        print('Skip refresh_finetuned due to existing output_flags:\n{}'.format('\n'.join(output_flags)))
        return user_name
    # download files for training
    downloaded_data_fnames = download_all_cloud_files_with_prefix(
        local_data_path_user,
        data_bucket.name, user_name,
        client, refresh_local=False
    )
    if not len(downloaded_data_fnames) > 0:
        raise ValueError('no data for user_name: {}'.format(user_name))

    # run the finetuning
    # this guy dumps model files in os.path.join(local_model_path_user, 'model')
    dump_finetuned(
        local_data_path_user, local_model_path_user,
        blocksize=blocksize, max_steps=maxsteps
    )

    # upload results
    _ = upload_all_local_files_with_prefix(
        os.path.join(local_model_path_user, 'model'),
        model_bucket.name, os.path.join(user_name, 'model'),
        client
    )

    # status cleanup
    status_progress.delete()
    status_success = status_bucket.blob(os.path.join(user_name, StatusFlags.model_training_success))
    status_success.upload_from_string('done')
    return user_name


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='finetune on user comments.')
    parser.add_argument('--users', type=str, nargs='*')
    parser.add_argument('--blocksize', type=int, default=16)
    parser.add_argument('--maxsteps', type=int, default=10)
    parser.add_argument('--forceupdate', type=bool, default=False)
    args = parser.parse_args()

    # list of users
    if args.users is None:
        with open('users.txt') as f:
            users = f.read().split()
    else:
        users = list(args.users)

    for user_name in users:
        print('user_name: {} running...'.format(user_name))
        ran = refresh_finetuned(user_name, blocksize=args.blocksize, maxsteps=args.maxsteps,
                                force_update=args.forceupdate)
        print('user_name: {} ran: {}'.format(user_name, ran))