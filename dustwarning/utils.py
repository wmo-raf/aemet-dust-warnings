import json
import logging
import os
import shutil
import stat
import tempfile
from datetime import datetime, timedelta

import requests

from dustwarning.config import SETTINGS
from dustwarning.errors import WarningsNotFound, WarningsRequestError

STATE_DIR = SETTINGS.get("STATE_DIR")
STATE_FILE = os.path.join(STATE_DIR, "state.json")
VERIFY_SSL = SETTINGS.get("VERIFY_SSL", True)


def copy_with_metadata(source, target):
    """Copy file with all its permissions and metadata.

    Lifted from https://stackoverflow.com/a/43761127/2860309
    :param source: source file name
    :param target: target file name
    """
    # copy content, stat-info (mode too), timestamps...
    shutil.copy2(source, target)
    # copy owner and group
    st = os.stat(source)
    os.chown(target, st[stat.ST_UID], st[stat.ST_GID])


def atomic_write(file_contents, target_file_path, mode="w"):
    """Write to a temporary file and rename it to avoid file corruption.
    Attribution: @therightstuff, @deichrenner, @hrudham
    :param file_contents: contents to be written to file
    :param target_file_path: the file to be created or replaced
    :param mode: the file mode defaults to "w", only "w" and "a" are supported
    """
    # Use the same directory as the destination file so that moving it across
    # file systems does not pose a problem.
    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        dir=os.path.dirname(target_file_path))
    try:
        # preserve file metadata if it already exists
        if os.path.exists(target_file_path):
            copy_with_metadata(target_file_path, temp_file.name)
        with open(temp_file.name, mode) as f:
            f.write(file_contents)
            f.flush()
            os.fsync(f.fileno())
        
        os.replace(temp_file.name, target_file_path)
    finally:
        if os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except:
                pass


def write_empty_state():
    content = {"last_update": ""}
    atomic_write(json.dumps(content, indent=4), STATE_FILE)
    return content


def read_state():
    # create state file if it does not exist
    if not os.path.isfile(STATE_FILE):
        with open(STATE_FILE, mode='w') as f:
            f.write("{}")
    try:
        logging.debug(f"[STATE]: Opening state file {STATE_FILE}")
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
    except json.decoder.JSONDecodeError:
        state = write_empty_state()
    
    return state


def update_state(last_update):
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    state.update({"last_update": last_update})
    
    atomic_write(json.dumps(state, indent=4), STATE_FILE)


def get_next_day(datetime_str):
    input_datetime = datetime.fromisoformat(datetime_str)
    next_day = input_datetime + timedelta(days=1)
    return next_day.replace(hour=0, minute=0, second=0, microsecond=0)


def get_json_warnings(url):
    try:
        response = requests.get(url, verify=VERIFY_SSL)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 404:
            raise WarningsNotFound(f"Warnings not found for {url}")
        else:
            raise WarningsRequestError(f"Error fetching warnings for {url}")
