# Script to run on server

from util import *
from buildmap import seed_blocks, seed_counties
import json
import io
import requests
import zipfile

def download_file(url):
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with io.open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
    return local_filename


def unzip(filename, dirname):
    zip_ref = zipfile.ZipFile(filename, 'r')
    zip_ref.extractall(dirname + "/")
    zip_ref.close()


def seed_census_api(state, granularity):
    """
    Build an initial node graph from US Census site.
    """
    print("Downloading state {} data".format(granularity))
    # Get state_id/state and use it to define file/directory names
    state_id, state_name = state.split('_', 1)
    filename = "tl_2009_{}_{}".format(state_id, granularity)
    dirname = "{}/".format(state_id)
    if not os.path.isdir(dirname):
        if not os.path.isfile(filename):
            download_file(US_CENSUS_API + state + "/" + filename + ".zip")
        unzip(filename + ".zip", dirname)
    print("Loading state {} data into memory".format(granularity))
    shape = fiona.open(dirname + filename + ".shp")
    return shape

