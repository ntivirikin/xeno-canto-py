from urllib import request, error
from urllib.request import urlretrieve
import urllib
import shutil
import errno
import json
import os
import time


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


def download(filt):
    page = 1
    page_num = 1
    path = metadata(filt)
    while page < page_num + 1:
        with open(path + '/page' + str(page) + ".json", 'r') as jsonfile:
            data = jsonfile.read()
        data = json.loads(data)
        page_num = data['numPages']
        for i in range(len((data['recordings']))):
            url = 'http:' + data['recordings'][i]['file']
            name = (data['recordings'][i]['en']).replace(' ', '')
            track_id = data['recordings'][i]['id']
            audio_path = 'dataset/audio/' + name + '/'
            audio_file = track_id + '.mp3'
            if not os.path.exists(audio_path):
                os.makedirs(audio_path)
            else:
                continue
            if os.path.exists(audio_path + audio_file):
                break
            urllib.request.urlretrieve(url, audio_path + audio_file)
        page += 1


# Scan directory for existing track id and write if found
# TODO: If track information cannot be found, check the database through track id
def scan_dir(directory, id_list, write_list):
    dir_temp = directory.replace(' ', '_')
    ilist = os.scandir(dir_temp)                                  
    for item in ilist:                                                        
                                                                               
        # Determine if item is a directory                                          
        if item.is_dir():                                                   
            scan_dir(item.path, id_list, write_list)                                                
        else:                                                                  
            odata = open(item.path)                                            
            jdata = json.load(odata)                                           

            for id_num in id_list:                                                                   
                for j in range(0, len(jdata["recordings"])):                        
                    if id_num == jdata["recordings"][j]["id"]:
                        track_id = jdata["recordings"][j]["id"]
                        species_j = jdata["recordings"][j]["gen"] + ' ' + jdata["recordings"][j]["sp"]
                        if jdata["recordings"][j]["ssp"] != '':
                            species_j += ' ' + jdata["recordings"][j]["ssp"]
                        species_j = species_j.replace('"', '')
                        write_list.append('{"id":' + track_id + ', "species":"' + species_j + '"}')
    return write_list

# Generate a metadata file for given library path
# TODO: Ensure consistent naming for gen, sp, and ssp tags
# TODO: Add ability to specify path of queries folder
def gen_meta(path=os.getcwd() + '/recordings/'):
    id_list = list()
    write_list = list()
    scan_list = os.scandir(path)                                               
                                                                               
    for scans in scan_list:                                                    
        filename = scans.name                                                  
        split_one = filename.split('_')
        split_two = split_one[1].split('.')
        ident = split_two[0]
        id_list.append(ident)                                                  
                                                                               
    # Scan queries folder path for track ids                              
    scan_string = scan_dir(os.getcwd() + '/queries/', id_list, write_list)
    meta_data = open('temp.txt', 'w+')
    meta_data.write('[' + ','.join(scan_string) + ']')
    meta_data.close()
    os.rename('temp.txt', 'metadata.json')


# TODO: Sort metadata by tag
