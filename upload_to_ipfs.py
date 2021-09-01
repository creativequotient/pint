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


def get_files(dir_path, exts=['.jpeg', '.jpg', '.png', '.gif', '.mp4', '.wav', '.gltf']):
    candidate_paths = os.listdir(dir_path)

    result = []

    for candidate in candidate_paths:
        for ext in exts:
            if candidate.endswith(ext):
                result.append(candidate)
                break

    return list(map(lambda rel_p: os.path.join(dir_path, rel_p), result))


def pin_with_pinata(fp):
    'Pin to Pinata by hash'

    with open(fp, 'rb') as file_to_upload:
        body = {
            'file': file_to_upload,
        }

        headers = {
            'pinata_api_key': credentials['API_Key'],
            'pinata_secret_api_key': credentials['API_Secret']
        }

        req = requests.post('https://api.pinata.cloud/pinning/pinFileToIPFS',
                            files=body,
                            headers=headers)
        file_to_upload.close()

    cid = req.json()['IpfsHash']

    if not req.ok:
        logger.error(f'Error encountered when pinning to pinata\n{req}')
        return False, _

    logger.info(f'Pinned {fp}')
    return True, cid


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Batch IPFS file uploading')
    parser.add_argument('-i', '--input', help='Path to directory containing media to upload', required=True)
    parser.add_argument('--pinata', action="store_true", default=False, help='Pin to pinata')
    args = vars(parser.parse_args())

    files_to_upload = sorted(get_files(args['input']))

    info = {}

    for idx, fp in enumerate(files_to_upload):
        name = os.path.basename(fp)
        is_successful, cid = pin_with_pinata(fp)
        if not is_successful:
            logger.error(f'{name} did not successfully get pinned')

        info[name] = {'cid': cid}

        if idx > 0 and idx % 500 == 0:
            with open(f'{args["input"]}/results_{idx}.json', 'w') as f:
                json.dump(info, f, indent=4)

    with open(f'{args["input"]}/results.json', 'w') as f:
        json.dump(info, f, indent=4)
