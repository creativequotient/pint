import argparse
import logging
import json
import tqdm
from tkinter import W
import requests
import os
import time
from dotenv import dotenv_values

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

credentials = dotenv_values(".env")


def unpin_from_pinata(cid):
    url = f'https://api.pinata.cloud/pinning/unpin/{cid}'

    headers = {
        'pinata_api_key': credentials['API_Key'],
        'pinata_secret_api_key': credentials['API_Secret']
    }

    req = requests.delete(url, headers=headers)

    if req.status_code != 200:
        logger.debug(req.content)
        return False

    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Batch IPFS file uploading')
    parser.add_argument('-i', '--input', help='Path to directory containing media to upload', required=True)
    args = vars(parser.parse_args())

    with open(args['input'], 'r') as f:
        ipfs_cids = list(map(lambda l: l.strip(), f.readlines()))
        f.close()

    for cid in ipfs_cids:

        try:
            is_unpinned = unpin_from_pinata(cid)

            if not is_unpinned:
                logger.error(f'{cid} did not successfully get unpinned')
                continue

            logger.info(f'Successfully unpinned {cid}')

        except Exception as e:
            print(e)
            continue
