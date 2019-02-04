import os
import urllib
import numpy as np
from tqdm.auto import tqdm

import FTPVeryBasicAuthHandler


# install a better handler for FTP requests capable of asking for and
# remembering passwords and reliably retrieving file sizes before downloads
FTPVeryBasicAuthHandler.setup()


def _download(url, local_file, bytes_per_chunk=1024*8, show_progress=True):
    '''

    '''

    with urllib.request.urlopen(url) as dist:
        with open(local_file, 'wb') as f:
            file_size_in_bytes = int(dist.headers['Content-Length'])
            num_chunks = int(np.ceil(file_size_in_bytes/bytes_per_chunk))
            if show_progress:
                pbar = tqdm(total=num_chunks*bytes_per_chunk, unit='B', unit_scale=True)
            while True:
                chunk = dist.read(bytes_per_chunk)
                if chunk:
                    f.write(chunk)
                    if show_progress:
                        pbar.update(bytes_per_chunk)
                else:
                    break
            if show_progress:
                pbar.close()


def safe_download(url, local_file, **kwargs):
    '''

    '''
    if not os.path.exists(local_file):
        print('Downloading {}'.format(os.path.basename(local_file)))
        _download(url, local_file, **kwargs)
    else:
        print('Skipping {} (already exists)'.format(os.path.basename(local_file)))
