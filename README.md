# Pint

Automatically pin files to IPFS via Pianta

## Quick start

### Set up configuration file

In the root directory of Pint, create a file named `credentials.py`
and define two variables - `API_KEY` and `SECRET_KEY` which correspond
to the credentials for your Pinata API.

### Uploading files

Run `python main.py -i <directory>` where `<directory>` is the
directory that contains all the assets to be uploaded. When
successful, a file named `results.json` will be written to
`<directory>` which contains the CID of each file uploaded.
