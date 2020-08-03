from astroturf.finetune import dump_finetuned

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='finetune on user comments.')
    parser.add_argument('--users', type=str, nargs='*')
    parser.add_argument('--blocksize', type=int, default=256)
    args = parser.parse_args()

    # list of users
    if args.users is None:
        with open('users.txt') as f:
            users = f.read().split()
    else:
        users = list(args.users)

    for user_name in users:
        inputpath = 'data/user/{}'.format(user_name)
        outputpath = 'finetune/{}'.format(user_name)
        ran = dump_finetuned(inputpath, outputpath, args.blocksize)
        print ('\n\nuser_name: {} ran?: {}\n\n'.format(user_name, ran))
