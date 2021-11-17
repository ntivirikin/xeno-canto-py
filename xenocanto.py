#!/usr/bin/python3

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple
from urllib import request, error
import sys
import shutil
import json
import os
import ssl
from tqdm.auto import tqdm

# TODO:
#   [/] Log messages to console
#   [X] Add ability to recognize the area where last download stopped
#   [ ] Purge recordings that did not complete download
#   [ ] Add sono image download capabilities
#   [ ] Display tables of tags collected
#
# FIXME:
#   [X] Fix naming of folders in audio and metadata to be more consistent
#   [X] Fix SSL certificate errors
#   [X] Fix stopping download when file present
#   [X] Fix using matches operator with tags (e.g. cnt:"United States")
#   [ ] Allow the delete method to accept species names with spaces

# Disable certificate verification
ssl._create_default_https_context = ssl._create_unverified_context


def read_json(json_loc):
    with open(json_loc) as f:
        return json.load(f)


def tqdmm(iterable: Iterable[Any], desc: str | None = None, **kwargs) -> tqdm:
    """
    Returns a custom progress bar - wrapper around tqdmm.

    Args:
        iterable (Iterable[Any]): Object to iterate on.
        desc (str, optional): Description of what's going on. Defaults to None.

    Returns:
        tqdm: progress bar.
    """
    return tqdm(
        iterable, desc=desc, leave=True, position=0, file=sys.stdout, **kwargs)


def metadata(
        filt: List[str],
        out_directory: str | os.PathLike = 'dataset') -> Path:
    """
    Download recording metadata (json file) for a given query.

    Args:
        filt (List[str]): List of query terms. 
            See `xeno-canto help <https://www.xeno-canto.org/help/search>`_.
        out_directory (str | os.PathLike): Where to save the metadata files.
            If str: a folder with this name will be created in your current 
            directory (i.e. where your code lives).
            If os.PathLike: a metadata folder will be created 
            in the provided directory.
            Defauls to 'dataset' to maintain compatibility.

    Returns:
        Path: Path to downloaded metadata.
    """

    filt_path, filt_url = [], []
    print("Retrieving metadata.")

    # Scrubbing input for file name and url
    for f in filt:
        filt_url.append(f.replace(' ', '%20'))
        filt_path.append((f.replace(' ', '')).replace(
            ':', '_').replace("\"", ""))

    path = Path(out_directory) / 'metadata' / ''.join(filt_path)

    # Overwrite metadata query folder
    if not path.exists():
        os.makedirs(path)

    # Save all pages of the JSON response
    page, page_num = 1, 1
    sepa = '%20'
    while page < page_num + 1:
        url = (
            "https://www.xeno-canto.org/api"
            f"/2/recordings?query={sepa.join(filt_url)}&page={page}")
        try:
            r = request.urlopen(url)
        except error.HTTPError as e:
            print('An error has occurred: ' + str(e))
            exit()
        print(f"Downloading metadata page {str(page)}.")
        data = json.loads(r.read().decode('UTF-8'))
        filename = path / f'page{str(page)}.json'
        with open(filename, 'w') as saved:
            json.dump(data, saved)
        page_num = data['numPages']
        page += 1

    # Return the path to the folder containing downloaded metadata
    return path


def _download_files(meta: List[Dict[str, Any]],
                    redown: Set, path: Path) -> Tuple[List[str],
                                                      List[str]]:

    # Gather already downloaded files and redownload files
    existing_files, redownload_files = [], []

    for data in tqdmm(meta, desc='Downloading files', total=len(meta)):

        # Keep track of the most recently downloaded file
        recent = open(path / "in_progress.txt", "w")
        recent.write(str(data['track_id'])), recent.write("\n")
        recent.close()

        # Redownload anything on progress files (might be corrupt)
        # FIXME: this is a slightly strange to deal with bad downloads.
        if int(data['track_id']) in redown:
            redownload_files.append(data['track_id'])
            request.urlretrieve(data['url'], data['filepath'])
            continue

        if not data['filepath'].parent.exists():
            os.makedirs(data['filepath'].parent)

        # If the file exists in the directory, we will skip it
        if data['filepath'].exists():
            existing_files.append(data['track_id'])
            continue

        request.urlretrieve(data['url'], data['filepath'])
    return existing_files, redownload_files


def download(
        filt: List[str],
        out_directory: str | os.PathLike = 'dataset') -> None:
    """
    Download recording metadata and audio files for a given query.

    Args:
        filt (List[str]): List of query terms. 
            See `xeno-canto help <https://www.xeno-canto.org/help/search>`_.
        out_directory (str | os.PathLike): Where to save the metadata and 
            sound files.
            If str: a folder with this name will be created in your current 
            directory (i.e. where your code lives).
            If os.PathLike: metadata and audio folders will be created 
            in the provided directory.
            Defauls to 'dataset' to maintain compatibility.
    """
    # Retrieve metadata to parse for download links
    path = metadata(filt, out_directory)
    metadata_dir = path.parents[0]

    # Enumerate list of metadata folders
    path_list, redown = _listdir_nohidden(metadata_dir), set()

    # Check for any in_progress files in the metadata folders
    for p in path_list:
        check_path = metadata_dir / str(p)
        if check_path.exists():
            continue
        progress_file = check_path / "in_progress.txt"
        if progress_file.exists():
            curr = open(progress_file)
            line = int(curr.readline())
            if line not in redown:
                redown.add(line)
            curr.close()

    audio_dir = path.parents[1] / 'audio'
    json_files = list(path.glob('page*.json'))
    recordings = [read_json(json)['recordings'] for json in json_files]
    recordings = [i for s in recordings for i in s]
    print(f'Found {len(recordings)} files matching your query, '
          'download will start:')

    meta = [
        {
            'url': 'http:' + recording['file'],
            'track_id': recording['id'],
            'filepath': (audio_dir /
                         recording['en'].replace(' ', '') /
                         f"{str(recording['id'])}.mp3")
        }
        for recording in recordings
    ]

    # Download files # TODO: parallelise this - v easy, ray or joblib?
    existing_files, redownload_files = _download_files(meta, redown, path)

    # Delete progress file if we make it this far
    os.remove(path / "in_progress.txt")

    # give feedback to user
    if len(existing_files):
        num_form = ['is', 'was'] if len(
            existing_files) == 1 else ['are', 'were']
        print(
            f"File(s) {[f'{file}.mp3' for file in existing_files]} "
            f"{num_form[0]} already present and {num_form[1]} skipped.")
    if len(redownload_files):
        print(
            f"File(s) {[f'{file}.mp3' for file in redownload_files]} "
            "had to be redownloaded (not completed during a previous query).")
    print('Done.')


def _listdir_nohidden(path: Path):
    """
    Retrieve all files while ignoring those that are hidden.

    Args:
        path (Path): Directory to search.

    Yields:
        str: Directory
    """
    for f in os.listdir(path):
        if not f.startswith('.'):
            yield f


def purge(num: int, out_directory: str | os.PathLike = 'dataset',
          verbose: bool = True) -> None:
    """
    Removes audio folders containing num or less than num files.
    #TODO: Option to do this before download might make more sense.

    Args:
        num (int): Minimum number of files.
        out_directory (str | os.PathLike): Where to save the metadata and 
            sound files.
            If str: a folder with this name will be created in your current 
            directory (i.e. where your code lives).
            If os.PathLike: metadata and audio folders will be created 
            in the provided directory.
            Defauls to 'dataset' to maintain compatibility.
        verbose (bool): Whether to print success message.
    """
    path = Path(out_directory) / 'audio'
    dirs = _listdir_nohidden(path)
    for fold in dirs:
        fold_path = path / fold
        count = sum(1 for _ in _listdir_nohidden(fold_path))
        if count < num:
            if verbose:
                print(
                    f"Folder at {fold_path} has fewer than {num} recordings. "
                    "Deleting.")
            shutil.rmtree(fold_path)


def delete(
        filt: List[str],
        out_directory: str | os.PathLike = 'dataset') -> None:
    """
    Delete recordings matching a given query.

    Args:
        filt (List[str]): List of query terms. 
            See `xeno-canto help <https://www.xeno-canto.org/help/search>`_.
        out_directory (str | os.PathLike): Where to save the metadata and 
            sound files.
            If str: a folder with this name will be created in your current 
            directory (i.e. where your code lives).
            If os.PathLike: metadata and audio folders will be created 
            in the provided directory.
            Defauls to 'dataset' to maintain compatibility.
    """

    # Generating list of current tracks with metadata
    gen_meta(out_directory=out_directory)
    metadata_dir = Path(out_directory) / 'metadata'
    path = Path(out_directory) / 'audio'

    # Separating desired tags from values for parsing
    tags, vals = [], []

    for f in filt:
        try:
            tag, val = f.split(':')[0], f.split(':')[1]
        except:
            # fails if item in list does not have search code,
            # I'll assume it's the eng name (in the package documentation
            # the english name is not prefixed with 'en:'
            tag = 'en'
            val = f
        if tag == 'en':
            val = val.replace('_', ' ')
        vals.append(val), tags.append(tag)

    data = read_json(metadata_dir / 'library.json')

    # Creating a set of track id's to delete
    track_del = set()
    for i in range(int(data['recordingNumber'])):
        for j in range(len(tags)):
            if data['tracks'][i][str(tags[j])] == str(vals[j]):
                track_del.add(int(data['tracks'][i]['id']))

    print(f'{len(track_del)} files scheduled for deletion.')

    # Checking audio folders for tracks to delete
    dirs = _listdir_nohidden(path)
    removed = 0
    for fold in dirs:
        fold_path = path / fold
        tracks = _listdir_nohidden(fold_path)
        for tr in tracks:
            if int(tr.split('.')[0]) in track_del:
                os.remove(fold_path / str(tr))
                removed += 1

    print(f"Deleted {str(removed)} files.")
    # Removing any empty folders
    purge(1, out_directory=out_directory, verbose=False)


def gen_meta(out_directory: str | os.PathLike = 'dataset'):
    """
    Generate a metadata file for given library path.

    Args:
        path (str, optional): [description]. Defaults to 'dataset'.
        out_directory (str | os.PathLike): Where to save the metadata.
            If str: a folder with this name will be created in your current 
            directory (i.e. where your code lives).
            If os.PathLike: metadata and audio folders will be created 
            in the provided directory.
            Defauls to 'dataset' to maintain compatibility.
    """
    # TODO Keeping this like it was, but strange - what's 'audio' doing here?
    path = Path(out_directory) / 'audio'
    library_dir = path / 'library.json'
    metadata_dir = Path(out_directory) / 'metadata'

    # Removing old library file if exists #REVIEW I don't get this
    if library_dir.exists():
        os.remove(library_dir)

    # Create a list of track IDs contained in the current library
    id_list = set()
    for fold in _listdir_nohidden(path):
        filenames = _listdir_nohidden(path / fold)
        for f in filenames:
            track_id = (f.split('.'))
            id_list.add(track_id[0])
    count = len(id_list)

    write_data = {'recordingNumber': str(count), 'tracks': []}

    # Create a list of all metadata files
    meta_files = [filename for filename in _listdir_nohidden(
        metadata_dir) if filename != 'library.json']

    # Check each metadata track for presence in library
    for f in meta_files:
        page_num, page = 1, 1
        while page < page_num + 1:
            # Open the json
            data = read_json(metadata_dir / f / f'page{str(page)}.json')
            page_num = data['numPages']

            # Parse through each track
            for i in range(len(data['recordings'])):
                track = data['recordings'][i]['id']
                if track in id_list:
                    track_info = data['recordings'][i]
                    write_data['tracks'].append(track_info)
            page += 1

    # Retrieves information from API for tracks that cannot be found in the
    # currently saved metadata
    found_files = list()
    for i in range(len(write_data['tracks'])):
        found_files.append(write_data['tracks'][i]['id'])

    not_found = list(set(id_list) - set(found_files))

    for i in not_found:
        track_find = f'nr:{i}'
        path = metadata([track_find])
        data = read_json(path / 'page1.json')
        write_data['tracks'].append(data['recordings'][0])

    with open('data.txt', 'w') as outfile:
        json.dump(write_data, outfile)
    os.rename('data.txt', metadata_dir / 'library.json')
    print("You can find the library metadata file at "
          f"{metadata_dir / 'library.json'}")


# ──── COMMAND LINE ENTRY POINT ─────────────────────────────────────────────────

def main():
    act = sys.argv[1]
    params = sys.argv[2:]

    if act == "-m":
        metadata(params)

    elif act == "-dl":
        download(params)

    elif act == "-p":
        purge(int(params[0]))

    elif act == "-g":
        if len(params) == 1:
            gen_meta(params[0])
        else:
            gen_meta()

    elif act == '-d':
        dec = input("Are you sure you want to proceed with "
                    "deleting? (Y or N)\n")
        if dec == "Y":
            delete(params)

    else:
        print("The command entered was not found, please consult the README "
              "for instructions and available commands.")


# Handles command line execution
if __name__ == '__main__':
    main()
