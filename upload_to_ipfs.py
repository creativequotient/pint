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


def get_files(dir_path, exts=['.jpeg', '.avi', '.jpg', '.png', '.gif', '.mp4', '.wav', '.gltf']):
    candidate_paths = os.listdir(dir_path)

    result = []

    for candidate in sorted(candidate_paths):
        for ext in exts:
            if candidate.endswith(ext):
                logger.info(f'Candidate for pinning found {candidate}')
                result.append(candidate)
                break

    return list(map(lambda rel_p: os.path.join(dir_path, rel_p), result))


def pin_with_pinata(fp):
    'Pin to Pinata by hash'

    logger.info(f'Attempting to pin {fp}')

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

    if not req.ok:
        logger.error(f'Error encountered when pinning to pinata\n{req.content}')
        return False, ''

    cid = req.json()['IpfsHash']

    logger.info(f'Successfully pinned {fp} with cid {cid}')

    return True, cid


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Batch IPFS file uploading')
    parser.add_argument('-i', '--input', help='Path to directory containing media to upload', required=True)
    parser.add_argument('-e', '--env', help='Path to .env file to load', required=False, default='.env')
    parser.add_argument('-o', '--override', help='Pin files from scratch, do not ignore files that have already been pinned', default=False, required=False, action='store_true')
    parser.add_argument('-r', '--reverse', help='Pin files in verse', default=False, required=False, action='store_true')
    args = vars(parser.parse_args())

    credentials = dotenv_values(args['env'])

    logger.info(f'Loading .env file from {args["env"]}')

    results_fp = f'{args["input"]}/results.json'

    files_to_upload = sorted(get_files(args['input']), reverse=args['reverse'])

    if os.path.exists(results_fp) and not args['override']:
        with open(results_fp, 'r') as f:
            info = json.load(f)
            f.close()
    else:
        info = {}

    for idx, fp in enumerate(files_to_upload):

        try:
            name = os.path.basename(fp)

            if name in info:
                if info[name]['cid'] != '':
                    logger.info(f'{name} already pinned')
                    continue

            is_successful, cid = pin_with_pinata(fp)

            if not is_successful:
                logger.error(f'{name} did not successfully get pinned')
                continue

            info[name] = {'cid': cid}

            with open(results_fp, 'w') as f:
                json.dump(info, f, indent=4)
                f.close()

        except Exception as e:
            print(e)
            continue
