#!/usr/bin/python3

import asyncio
import json
import os
import shutil
import sys
import time
from urllib import request, error

import aiofiles
import aiohttp


# TODO:
#   [X] Log messages to console
#   [ ] Add sono image download capabilities
#   [ ] Add ability to process multiple species in one command
#   [ ] Create function to verify all recordings downloaded correctly
#   [ ] Purge recordings that did not complete download
#   [ ] Add text file processing for batch requests
#   [ ] Display tables of tags collected
#
# FIXME:
#   [ ] Modify delete method to remove recordings containing all input tags
#       rather than any one of the tags
#   [ ] Allow the delete method to accept species names with spaces


# Retrieves metadata for requested recordings in the form of a JSON file
def metadata(filt):
    page = 1
    page_num = 1
    filt_path = list()
    filt_url = list()
    print("Retrieving metadata...")

    # Scrubbing input for file name and url
    for f in filt:
        filt_url.append(f.replace(' ', '%20'))
        filt_path.append((f.replace(' ', '')).replace(':', '_')
                         .replace('\"', ''))

    path = 'dataset/metadata/' + ''.join(filt_path)

    # Create a metadata folder if it does not exist already
    if not os.path.exists(path):
        os.makedirs(path)

    # Input parameters are separated by %20 for use in URL
    query = ('%20'.join(filt_url))

    # Save all pages of the JSON response
    while page < (page_num + 1):
        url = ('https://www.xeno-canto.org/api/2/recordings?'
               'query={0}&page={1}'.format(query, page))
        try:
            r = request.urlopen(url)
        except error.HTTPError as e:
            print("An error has occurred: " + str(e))
            exit()
        print("Downloading metadata page " + str(page) + "...")
        data = json.loads(r.read().decode('UTF-8'))
        filename = path + '/page' + str(page) + '.json'
        with open(filename, 'w') as saved:
            json.dump(data, saved)
        page_num = data['numPages']
        page += 1

        # Rate limit of one request per second
        time.sleep(1)

    # Return the path to the folder containing downloaded metadata
    print("Metadata retrieval complete.")
    return path


# Uses JSON metadata files to generate a list of recording URLs
def list_urls(path):
    url_list = []
    page = 1

    # Initial opening of JSON to retrieve amount of pages and recordings
    with open(path + '/page' + str(page) + '.json', 'r') as jsonfile:
        data = jsonfile.read()
        jsonfile.close()
    data = json.loads(data)
    page_num = data['numPages']
    recordings_num = int(data['numRecordings'])

    # Clear may not be required if setting to None, included for redundancy
    data.clear()
    data = None

    # Set the first element to the number of recordings
    url_list.append(recordings_num)

    # Second element will be a list of tuples with (name, track_id, file url)
    url_list.append(list())

    # Read each metadata file and extract information into list as a tuple
    while page < page_num + 1:
        with open(path + '/page' + str(page) + '.json', 'r') as jsonfile:
            data = jsonfile.read()
            jsonfile.close()
        data = json.loads(data)

        # Extract the number of recordings in the opened metadata file
        rec_length = len(data['recordings'])

        # Parse through the opened data and add it to the URL list
        for i in range(0, rec_length):
            name = (data['recordings'][i]['en']).replace(' ', '')
            track_id = data['recordings'][i]['id']
            track_url = data['recordings'][i]['file']
            track_info = (name, track_id, track_url)
            url_list[1].append(track_info)
        page += 1
    return url_list


# Client that processes the list of track information concurrently
def chunked_http_client(num_chunks):

    # Semaphore used to limit the number of requests with num_chunks
    semaphore = asyncio.Semaphore(num_chunks)

    # Processes a tuple from the url_list using the aiohttp client_session
    async def http_get(track_tuple, client_session):

        # Work with semaphore located outside the function
        nonlocal semaphore
        async with semaphore:

            # Pull relevant info from tuple
            name = str(track_tuple[0])
            track_id = str(track_tuple[1])
            url = track_tuple[2]

            # Set up the paths required for saving the audio file
            folder_path = 'dataset/audio/' + name + '/'
            file_path = folder_path + track_id + '.mp3'

            # Create an audio folder for the species if it does not exist
            if not os.path.exists(folder_path):
                print("Creating recording folder at " + str(folder_path))
                os.makedirs(folder_path)

            # If the file exists in the directory, we will skip it
            if os.path.exists(file_path):
                print(track_id + ".mp3 is already present. Skipping...")
                return

            # Use the aiohttp client to retrieve the audio file asynchronously
            async with client_session.get(url) as response:
                if response.status == 200:
                    f = await aiofiles.open((file_path), mode='wb')
                    await f.write(await response.content.read())
                    await f.close()
                elif response.status == 503:
                    print("Error 503 occurred when downloading " + track_id +
                          ".mp3. Please try using a lower value for "
                          "num_chunks. Consult the README for more "
                          "information.")
                else:
                    print("Error " + str(response.status) + " occurred "
                          "when downloading " + track_id + ".mp3.")

    return http_get


# Retrieves metadata and recordings for a given set of input param
async def download(filt, num_chunks=4):

    # Retrieve metadata and generate list of track information
    meta_path = metadata(filt)
    url_list = list_urls(meta_path)

    # Retrieve the number of recordings to be downloaded
    recordings_num = url_list[0]

    # Exit the program if no recordings are found
    if (recordings_num == 0):
        print("No recordings found for the provided request.")
        quit()

    print(str(recordings_num) + " recordings found, downloading...")

    # Setup the aiohttp client with the desired semaphore limit
    http_client = chunked_http_client(num_chunks)
    async with aiohttp.ClientSession() as client_session:

        # Collect tasks and await futures to ensure concurrent processing
        tasks = [http_client(track_tuple, client_session) for track_tuple in
                 url_list[1]]
        for future in asyncio.as_completed(tasks):
            data = await future
    print("Download complete.")


# Retrieve all files while ignoring those that are hidden
def listdir_nohidden(path):
    for f in os.listdir(path):
        if not f.startswith('.'):
            yield f


# Removes audio folders containing num or less than num files
def purge(num):
    print("Removing all audio folders with fewer than " + str(num) +
          " recordings.")
    path = 'dataset/audio/'
    dirs = listdir_nohidden(path)
    remove_count = 0

    # Count the number of tracks in each folder
    for fold in dirs:
        fold_path = path + fold
        count = sum(1 for _ in listdir_nohidden(fold_path))

        # Remove the folder if the track amount is less than input
        if count < num:
            print("Deleting " + fold_path + " since <" + str(num) + " tracks.")
            shutil.rmtree(fold_path)
            remove_count = remove_count + 1
    print(str(remove_count) + " folders removed.")


# Deletes audio tracks based on provided parameters
def delete(filt):

    # Generating list of current tracks with metadata
    gen_meta()

    # Separating desired tags from values for parsing
    tags = list()
    vals = list()
    for f in filt:
        tag = f.split(':')[0]
        tags.append(tag)

        val = f.split(':')[1]
        if tag == 'en':
            val = val.replace('_', ' ')
        vals.append(val)

    with open('dataset/metadata/library.json', 'r') as jsonfile:
        data = jsonfile.read()
    data = json.loads(data)

    # Creating a set of track id's to delete
    track_del = set()
    for i in range(int(data['recordingNumber'])):
        for j in range(len(tags)):
            if data['tracks'][i][str(tags[j])] == str(vals[j]):
                track_del.add(int(data['tracks'][i]['id']))

            # Proposed change for deletion of tracks matching all inputs
            # rather than any
            #
            # if data['tracks'][i][str(tags[j])] != str(vals[j]):
                # exit this for loop
            # track_del.add(int(data['tracks'][i]['id']))

    print(str(len(track_del)) + " tracks have been identified to be deleted.")

    # Checking audio folders for tracks to delete
    path = 'dataset/audio/'
    dirs = listdir_nohidden(path)
    removed = 0
    for fold in dirs:
        fold_path = path + fold
        tracks = listdir_nohidden(fold_path)
        for tr in tracks:
            if int(tr.split('.')[0]) in track_del:
                os.remove(fold_path + '/' + str(tr))
                removed = removed + 1

    print(str(removed) + " tracks deleted!")

    # Removing any empty folders
    purge(1)


# Generate a metadata file for given library path
def gen_meta(path='dataset/audio/'):

    # Checking to see if the path exists
    if not os.path.exists(path):
        print("Path " + str(path) + " does not exist.")
        return
    print("Generating metadata file for current recording library...")

    # Removing old library file if exists
    if os.path.exists('dataset/metadata/library.json'):
        os.remove('dataset/metadata/library.json')

    # Create a list of track ID's contained in the current library
    id_list = set()

    for fold in listdir_nohidden(path):
        filenames = listdir_nohidden(path + fold)
        for f in filenames:
            track_id = (f.split('.'))
            id_list.add(track_id[0])

    count = len(id_list)
    print(str(count) + " recordings have been found. Collecting metadata...")

    write_data = dict()
    write_data['recordingNumber'] = str(count)
    write_data['tracks'] = list()

    # Create a list of all metadata files
    meta_files = list()
    if os.path.exists('dataset/metadata/'):
        for filename in listdir_nohidden('dataset/metadata/'):
            if filename != 'library.json':
                meta_files.append(filename)

    # Check each metadata track for presence in library
    found_files = set()
    for f in meta_files:
        page_num = 1
        page = 1

        while page < page_num + 1:

            # Open the json
            with open('dataset/metadata/' + f + '/page' + str(page) +
                      '.json', 'r') as jsonfile:
                data = jsonfile.read()
            data = json.loads(data)
            page_num = data['numPages']

            # Parse through each track
            for i in range(len(data['recordings'])):
                track = data['recordings'][i]['id']
                if track in id_list:
                    track_info = data['recordings'][i]
                    write_data['tracks'].append(track_info)
            page += 1

    # Retrieves information from  API for tracks that cannot be found in the
    # currently saved metadata
    found_files = list()
    for i in range(len(write_data['tracks'])):
        found_files.append(write_data['tracks'][i]['id'])

    not_found = list(set(id_list) - set(found_files))
    if not_found:
        print(str(len(not_found)) + " recordings must have their "
              " metadata downloaded.")

    # Retrieves metadata for each of the recordings individually
    for i in not_found:
        track_find = 'nr:' + i
        path = metadata([track_find])
        with open(path + '/page1.json') as jsonfile:
            data = jsonfile.read()
        data = json.loads(data)
        write_data['tracks'].append(data['recordings'][0])

    with open('data.txt', 'w') as outfile:
        json.dump(write_data, outfile)

    os.rename('data.txt', 'dataset/metadata/library.json')
    print("Metadata successfully generated at dataset/metadata/library.json")


# Accepts command line input to determine function to execute
def main():
    if len(sys.argv) == 1:
        print("No command given. Please consult the README for help.")
        return

    if len(sys.argv) == 2:
        print("Commands must be given in a '-command parameter' format. "
              "Please consult the README for help.")

    act = sys.argv[1]
    params = sys.argv[2:]

    # Retrieve metadata
    if act == "-m":
        metadata(params)

    # Download recordings
    elif act == "-dl":
        start = time.time()
        asyncio.run(download(params))
        end = time.time()
        print("Duration: " + str(int(end - start)) + "s")

    # Purge folders
    elif act == "-p":
        purge(int(params[0]))

    # Generate library metadata
    elif act == "-g":
        if len(params) == 1:
            gen_meta(params[0])
        else:
            gen_meta()

    # Delete recordings matching ANY input parameter
    elif act == '-del':
        dec = input("Proceed with deleting? (Y or N)\n")
        if dec == "Y":
            delete(params)

    else:
        print("Command not found, please consult the README.")


# Handles command line execution
if __name__ == '__main__':
    main()
