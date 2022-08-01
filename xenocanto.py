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
#   [/] Log messages to console
#   [X] Add concurrent execution of recording downloads using asyncio
#   [ ] Add sono image download capabilities
#   [ ] Add ability to process multiple species in one command
#   [ ] Create function to verify all recordings downloaded correctly
#   [ ] Purge recordings that did not complete download
#   [ ] Add text file processing for batch requests
#   [ ] Display tables of tags collected
#
# FIXME:
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
        filt_path.append((f.replace(' ', '')).replace(':', '_').replace("\"",""))

    path = 'dataset/metadata/' + ''.join(filt_path)

    # Create a metadata folder if it does not exist already
    if not os.path.exists(path):
        os.makedirs(path)

    # Save all pages of the JSON response
    while page < (page_num + 1):
        url = 'https://www.xeno-canto.org/api/2/recordings?query={0}&page={1}'.format('%20'.join(filt_url), page)
        try:
            r = request.urlopen(url)
        except error.HTTPError as e:
            print('An error has occurred: ' + str(e))
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
    print('Metadata retrieval completed.')
    return path


# Uses JSON metadata files to generate a list of recording URLs for easier processing by download(filt)
def list_urls(path):
    url_list = []
    page = 1
    
    # Initial opening of JSON to retrieve amount of pages and recordings
    with open(path + '/page' + str(page) + ".json", 'r') as jsonfile:
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

    # Second element will be a list of tuples with three elements each (name, track_id, file url)
    url_list.append(list())

    # Read each metadata file and extract information into list as a tuple
    while page < page_num + 1:
        with open(path + '/page' + str(page) + '.json', 'r') as jsonfile:
            data = jsonfile.read()
            jsonfile.close()
        data = json.loads(data)

        # Extract the number of recordings in the opened metadata file
        rec_length = len(data["recordings"])

        # Parse through the opened data and add it to the URL list
        for i in range(0, rec_length):
            name = (data['recordings'][i]['en']).replace(' ', '')
            track_id = data['recordings'][i]['id']
            track_url = data['recordings'][i]['file']
            track_info = (name, track_id, track_url)
            url_list[1].append(track_info)
        page += 1
    return url_list


# This is the client that will process the list of track information concurrently
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
            audio_path = 'dataset/audio/' + name + '/'
            audio_file = track_id + '.mp3'

            # Create an audio folder for the species if it does not exist
            if not os.path.exists(audio_path):
                os.makedirs(audio_path)

            # If the file exists in the directory, we will skip it
            if os.path.exists(audio_path + audio_file):
                print(track_id + ".mp3 is already present. Continuing...")
                return

            # Use the aiohttp client_session to retrieve the audio file asynchronously
            async with client_session.get(url) as response:
                print("Start request at " + str(time.time()))
                if response.status == 200:
                        f = await aiofiles.open((audio_path + audio_file), mode='wb')
                        await f.write(await response.content.read())
                        await f.close()
                else:
                    print("Error occurred: " + str(response.status))

    return http_get


# Retrieves metadata and recordings for a given set of input param
async def download(filt):

    # Retrieve metadata and generate list of track information
    meta_path = metadata(filt)
    url_list = list_urls(meta_path)

    # Retrieve the number of recordings to be downloaded
    recordings_num = url_list[0]
    print(str(recordings_num) + " recordings found, downloading...")
    
    # Setup the aiohttp client with the desired semaphore limit
    http_client = chunked_http_client(5)
    async with aiohttp.ClientSession() as client_session:

        # Collect the required tasks and await futures to ensure concurrent processing
        tasks = [http_client(track_tuple, client_session) for track_tuple in  url_list[1]]
        for future in asyncio.as_completed(tasks):
            data = await future


# Retrieve all files while ignoring those that are hidden
def listdir_nohidden(path):
    for f in os.listdir(path):
        if not f.startswith('.'):
            yield f


# Removes audio folders containing num or less than num files
def purge(num):
    path = 'dataset/audio/'
    dirs = listdir_nohidden(path)
    for fold in dirs:
        fold_path = path + fold
        count = sum(1 for _ in listdir_nohidden(fold_path))
        if count < num:
            print("Folder at " + fold_path + " has fewer than " + str(num) + " recordings. Deleting...")
            shutil.rmtree(fold_path)


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

    # Removing old library file if exists
    if os.path.exists(path + 'library.json'):
        os.remove(path + 'library.json')

    # Create a list of track ID's contained in the current library
    id_list = set()

    for fold in listdir_nohidden(path):
        filenames = listdir_nohidden(path + fold)
        for f in filenames:
            track_id = (f.split('.'))
            id_list.add(track_id[0])
    
    count = len(id_list)

    write_data = dict()
    write_data['recordingNumber'] = str(count)
    write_data['tracks'] = list()

    # Create a list of all metadata files
    meta_files = list()
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
            with open('dataset/metadata/' + f + '/page'+ str(page)  + ".json", 'r') as jsonfile:
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


# Accepts command line input to determine function to execute
def main():
    act = sys.argv[1]
    params = sys.argv[2:]
 
    if act == "-m":
        metadata(params)

    elif act == "-dl":
        start = time.time()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(download(params))
        end = time.time()
        print("Time elapsed: " + str((end - start)))

    elif act == "-p":
        purge(int(params[0]))

    elif act == "-g":
        if len(params) == 1:
            gen_meta(params[0])
        else:
            gen_meta()

    elif act == '-d':
        dec = input("Are you sure you want to proceed with deleting? (Y or N)\n")
        if dec == "Y":
            delete(params)
            
    else:
        print("The command entered was not found, please consult the README for instructions and available commands.")


# Handles command line execution
if __name__ == '__main__':
    main()
