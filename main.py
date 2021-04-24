import argparse
import logging
import json
import subprocess
import requests
import os
from credentials import API_KEY, SECRET_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        'pinata_api_key': API_KEY,
        'pinata_secret_api_key': SECRET_KEY
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

        is_successful = pin_with_pinata(cid, name)

        if is_successful:
            info[name] = {'cid': cid}

    with open(f'{args["input"]}/results.json', 'w') as f:
        json.dump(info, f, indent=4)
