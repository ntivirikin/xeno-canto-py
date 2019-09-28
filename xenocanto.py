from urllib import request, error
import shutil
import json
import os


# Retrieves metadata for requested recordings in the form of a JSON file
def metadata(filt):
    page = 1
    page_num = 1

    # Scrubbing input for file name and url
    filt_path = list()
    for f in filt:
        scrubbed = (f.replace(' ', '')).replace(':', '_')
        filt_path.append(scrubbed)
    filt_url = list()
    for f in filt:
        scrubbed = f.replace(' ', '%20')
        filt_url.append(scrubbed)
    path = 'dataset/metadata/' + '&'.join(filt_path)
    if not os.path.exists(path):
        os.makedirs(path)
    else:
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

    # Retrieve metadata to parse for download links
    path = metadata(filt)
    while page < page_num + 1:
        with open(path + '/page' + str(page) + ".json", 'r') as jsonfile:
            data = jsonfile.read()
        data = json.loads(data)
        page_num = data['numPages']

        # Pulling species name, track ID, and download link for naming and retrieval
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
            request.urlretrieve(url, audio_path + audio_file)
        page += 1

# Generate a metadata file for given library path
def gen_meta(path='/dataset/audio/'):
    
    # Create a list of track ID's contained in the current library
    id_list = set()
    for fold in os.listdir(path):
        filenames = os.listdir(fold)
        for f in filenames:
            track_id = (f.split('.'))[0]
            id_list.update(track_id)
    
    # Create a list of all metadata files
    meta_files = list()
    for filename in os.listdir('/dataset/metadata/'):
        meta_files.append(filename)
    
    # Check each metadata track for presence in library
    found_files = set()
    for f in meta_files:

        # Open the json file up
        with open('dataset/metadata/' + f + '/page') + ".json", 'r') as jsonfile:
            data = jsonfile.read()
        data = json.loads(data)
        page_num = data['numPages']
        
        # Parse through each track
        for i in range(len(data['recordings'])):
            track = data['recordings'][0]['track_id'] 
            if track in id_list:
                found_files.update(track)

    not_found = list(id_list - found_files)
    for i in not_found:
        path = metadata('nr:' + i)

    

# Removes audio folders containing num or less than num files
def purge(num):
    path = 'dataset/audio/'
    dirs = os.listdir(path)
    for fold in dirs:
        fold_path = path + fold
        count = len(os.listdir(fold_path))
        if count <= num:
            shutil.rmtree(fold_path)
