from urllib import request, error
from datetime import datetime
import shutil
import errno
import json
import os
import time


# Prints error message to user when caught
def err_log(error):
    date = str(datetime.utcnow())
    errmsg = '[' + date + '] ' + str(error) + ' occurred.'
    print(errmsg)


# Creates directory, ignores 'already exists' errors
def create_dir(directory):
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            err_log(e)
            raise


# Retrieves metadata for requested recordings in the form of a JSON file
def metadata(filt):
    page = 1
    numPages = 1

    # Scrubbing input for file name and url
    filt_path = list()
    for f in filt:
        f = (f.replace(' ', '')).replace(':', '_')
        filt_path.append(f)

    filt_url = list()
    for f in filt:
        f = f.replace(' ', '%20')
        filt_url.append(f)

    path = 'dataset/metadata/' + '&'.join(filt_path)
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        print('The specified query folder already exists, please + \
            rename or remove the folder from the directory and try again.')
        exit()

    # Save all pages of the JSON response    
    while page < numPages + 1:
        url = 'https://www.xeno-canto.org/api/2/recordings?query={0}&page={1}'.format('%20'.join(filt_url), page)
        try:
            r = request.urlopen(url)
        except error.HTTPError as e:
            err_log(e)
            exit()
        data = json.loads(r.read().decode('UTF-8'))
        filename = path + '/page' + str(page) + '.json'
        with open(filename, 'w') as saved:
            json.dump(data, saved)
        numPages = data['numPages']
        page += 1

    # Return the path to the folder containing downloaded metadata
    return path


# Retrieves recording based on list of downloaded JSON file paths
def get_mp3(paths):
    # Creating folder structure and reserving temp path
    folder = os.getcwd() + '/recordings/'
    mp3_list = []
    create_dir(folder)
    temp_mp3 = folder + 'temp.mp3'

    # Parsing all JSON files for download links and executing them
    for file in paths:
        json_file = open(file)
        data = json.load(json_file)
        json_file.close()

        for i in range(0, int(data["numRecordings"])):
            rec_path = (str(folder) +
                        data["recordings"][i]["en"].replace(' ', '') +
                        '_' + data["recordings"][i]["id"] + '.mp3')

            if (os.path.exists(rec_path)) is False:
                url = 'https:' + data["recordings"][i]["file"]
                try:
                    r = request.urlopen(url)
                except error.HTTPError as e:
                    err_log(e)
                    continue
                mp3_data = r.read()
                mp3 = open(temp_mp3, 'wb')
                mp3.write(mp3_data)
                mp3.close
                os.rename(temp_mp3, rec_path)
                mp3_list.append(rec_path)
                
    # Returns string list of downloaded recording file paths
    return mp3_list


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
