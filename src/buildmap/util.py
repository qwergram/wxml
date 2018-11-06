import io
import requests
import zipfile

# For LOGGER
VERBOSE = False

def log(*args, **kwargs):
    if VERBOSE:
        print('[!]', *args, **kwargs)