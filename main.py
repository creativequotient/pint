import argparse
import logging
import json
import subprocess
import requests
import os
import time
from dotenv import dotenv_values

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

credentials = dotenv_values(".env")


def get_files(dir_path, exts=['.jpeg', '.jpg', '.png', '.gif', '.mp4']):
    candidate_paths = os.listdir(dir_path)

    result = []

    for candidate in candidate_paths:
        for ext in exts:
            if candidate.endswith(ext):
                result.append(candidate)
                break

    return list(map(lambda rel_p: os.path.join(dir_path, rel_p), result))


def ipfs_add_local(file_path):
    'Returns CID by pinning locally'

    proc = subprocess.run(['ipfs', 'add', file_path], capture_output=True, text=True)

    logger.debug(proc.stdout)
    logger.info(f'Added {file_path} to IPFS')

    return proc.stdout.split()[1]


def pin_with_pinata(cid, name):
    'Pin to Pinata by hash'

    body = {
        'hashToPin': cid,
        'pinataMetadata': {
            'name': name
        }
    }

    headers = {
        'pinata_api_key': credentials['API_Key'],
        'pinata_secret_api_key': credentials['API_Secret']
    }

    req = requests.post('https://api.pinata.cloud/pinning/pinByHash',
                        json=body,
                        headers=headers)

    if not req.ok:
        logger.error(f'Error encountered when pinning to pinata\n{req}')
        return False

    logger.info(f'Pinned {name} with cid {cid} to Pinata')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Batch IPFS file uploading')
    parser.add_argument('-i', '--input', help='Path to directory containing media to upload', required=True)
    parser.add_argument('--pinata', action="store_true", default=False, help='Pin to pinata')
    args = vars(parser.parse_args())

    files_to_upload = sorted(get_files(args['input']))

    info = {}

    for fp in files_to_upload:
        # Add image to IPFS locally
        cid = ipfs_add_local(fp)

        if cid == '':
            continue

        # Get name of file
        name = os.path.basename(fp)

        if args['pinata']:
            # Sleep to circumvent Pinata rate limitation
            time.sleep(0.75)
            is_successful = pin_with_pinata(cid, name)
            if not is_successful:
                logger.error(f'{name} did not successfully get pinned')

        info[name] = {'cid': cid}

    with open(f'{args["input"]}/results.json', 'w') as f:
        json.dump(info, f, indent=4)
