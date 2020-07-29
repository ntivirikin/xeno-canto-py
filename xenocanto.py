#!/usr/bin/python3

from urllib import request, error
import sys
import shutil
import json
import os
import ssl

# TODO: 
#   [/] Log messages to console
#   [ ] Add ability to recognize the area where last download stopped
#   [ ] Add sono image download capabilities
#   [ ] Display tables of tags collected
#
# FIXME:
#   [ ] Fix naming of folders in audio and metadata to be more consistent
#   [X] Fix SSL certificate errors
#   [ ] Fix stopping download when file present
#   [X] Fix using matches operator with tags (e.g. cnt:"United States")

# Disable certificate verification
ssl._create_default_https_context = ssl._create_unverified_context

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

    # Overwrite metadata query folder 
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

    # Save all pages of the JSON response    
    while page < page_num + 1:
        url = 'https://www.xeno-canto.org/api/2/recordings?query={0}&page={1}'.format('%20'.join(filt_url), page)
        try:
            r = request.urlopen(url)
        except error.HTTPError as e:
            print('An error has occurred: ' + str(e))
            exit()
        print("Downloading metadate page " + str(page) + "...")
        data = json.loads(r.read().decode('UTF-8'))
        filename = path + '/page' + str(page) + '.json'
        with open(filename, 'w') as saved:
            json.dump(data, saved)
        page_num = data['numPages']
        page += 1

    # Return the path to the folder containing downloaded metadata
    return path


# Retrieves metadata and audio recordings
def download(filt):
    page = 1
    page_num = 1
    print("Downloading all recordings for query...")

    # Retrieve metadata to parse for download links
    path = metadata(filt)
    with open(path + '/page' + str(page) + ".json", 'r') as jsonfile:
        data = jsonfile.read()
    data = json.loads(data)
    page_num = data['numPages']
    print("Found " + str(data['numRecordings']) + " recordings for given query, downloading...") 
    while page < page_num + 1:

        # Pulling species name, track ID, and download link for naming and retrieval
        # while i < range(len)


        for i in range(len((data['recordings']))):
            url = 'http:' + data['recordings'][i]['file']
            name = (data['recordings'][i]['en']).replace(' ', '')
            track_id = data['recordings'][i]['id']
            audio_path = 'dataset/audio/' + name + '/'
            audio_file = track_id + '.mp3'
            if not os.path.exists(audio_path):
                os.makedirs(audio_path)

            # If the file exists in the directory, we will skip it
            elif os.path.exists(audio_path + audio_file):
                break
            print("Downloading " + track_id + ".mp3...")
            request.urlretrieve(url, audio_path + audio_file)
        page += 1

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
            shutil.rmtree(fold_path)


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

    # Checking audio folders for tracks to delete
    path = 'dataset/audio/'
    dirs = listdir_nohidden(path)
    for fold in dirs:
        fold_path = path + fold
        tracks = listdir_nohidden(fold_path)
        for tr in tracks:
            if int(tr.split('.')[0]) in track_del:
                os.remove(fold_path + '/' + str(tr))

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
        delete(params)
            
    else:
        print("The command entered was not found, please consult the README for instructions and available commands.")


# Handles command line execution
if __name__ == '__main__':
    main()
