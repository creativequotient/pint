import argparse
import logging
import json
import subprocess
import requests
import os
import pathlib
import pprint
import time
import typing as tp
from dotenv import dotenv_values

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

credentials = dotenv_values(".env")


def pin_with_pinata(body):
    'Pin to Pinata by hash'

    headers = {
        'pinata_api_key': credentials['API_Key'],
        'pinata_secret_api_key': credentials['API_Secret']
    }

    req: requests.Response = requests.post('https://api.pinata.cloud/pinning/pinFileToIPFS',
                                           files=body,
                                           headers=headers)

    if not req.ok:
        logger.error(f'Error encountered when pinning to pinata\n{req.content}')
        return False, ''

    cid = req.json()['IpfsHash']

    logger.info(f'Successfully pinned {fp} with cid {cid}')

    return True, cid


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Batch IPFS file uploading')
    parser.add_argument('-i', '--input', help='Path to directory containing media to upload', required=True)
    args = vars(parser.parse_args())

    results_fp = f'{args["input"]}/results.json'

    paths: tp.List[str] = []

    dir_name = os.path.basename(args['input'])

    for root, dirs, files in os.walk(os.path.abspath(args['input'])):
        for fn in files:
            paths.append(os.path.join(root, fn))

    paths = sorted(paths)

    pprint.pprint(paths)

    files = []

    for fp in paths:
        with open(fp, 'rb') as f:
            dir_path = os.path.join(pathlib.Path(fp).parent.stem, pathlib.Path(fp).stem)
            print(dir_path)
            files.append(('file', (dir_path, f.read())))
            f.close()

    success, cid = pin_with_pinata(files)

    if success:
        logger.info(f'Directory successfully pinned with CID {cid}')

    else:
        logger.info(f'Directory was not pinned successfully')
