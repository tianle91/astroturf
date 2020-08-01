from astroturf.finetune import dump_finetuned

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='finetune on user comments.')
    parser.add_argument('--users', type=str, nargs='*')
    parser.add_argument('--blocksize', type=int, default=256)
    args = parser.parse_args()

    blocksize = args.blocksize
    for user_name in args.users:
        inputpath = 'data/user/{}'.format(user_name)
        outputpath = 'finetune/{}'.format(user_name)
        print ('\n\nuser_name: {} ran?: {}\n\n'.format(
            user_name, 
            dump_finetuned(inputpath, outputpath, blocksize)
        ))
