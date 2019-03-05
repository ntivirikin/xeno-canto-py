# Library management
# Filtering and returning lists of files based on criteria
from xenocanto import create_dir
from urllib import request
import shutil
import os
import json
import error

filter_lib(os.getcwd(), ['q:A'])

# Filter for any tags included in .json
def filter_lib(path, criteria):
    create_dir(os.getcwd() + '/filtered/')
    temp_list = []
    for root, dirs, files in os.walk(path):
        for name in files:
            load = json.load(os.path.join(root, name))
            for i in range(0, len(load["recordings"])):
                for j in criteria:
                    res = j.split(':')
                    if load["recordings"][i][res[0]] == res[1]:
                        temp_list.append((load["recordings"][i]["en"]).replace(' ', '') + load["recordings"][i]["id"] + '.mp3')
            load.close()
    for i in temp_list:
        shutil.copy2(os.getcwd() + '/recordings/' + i, os.getcwd() + '/filtered/' + i)
    return temp_list
    

# This is separate because it needs to connect to internet (only in advanced, can be bypassed by putting this into get_recordings)
def filter_background(background):
    url = 'https://www.xeno-canto.org/api/2/recordings?query='
    for val in background:
        url += val + '%20'
    try:
        r = request.urlopen(url)
    except error.HTTPError:
        print('Error: 404! ' + url + ' does not exist!')
    data = r.read()
    data_json = json.loads(data.decode('utf-8'))

    # Retrieve queries as .json files for all pages
    pages = data_json["numPages"]
    temp_list = []
    for i in range(1, pages + 1):
        url = 'https://www.xeno-canto.org/api/2/recordings?query='
        for val in background:
            url += val + '%20'
        url += '&page=' + str(i)
        r = request.urlopen(url)
        data = r.read()
        data_json = json.loads(data.decode('utf-8'))
        for i in range(0, len(data_json["recordings"])):
            temp_list.append((data_json["recordings"][i]["en"]).replace(' ', '') + data_json["recordings"][i]["id"] + '.mp3')
        data_json.close()

        for i in temp_list:
            shutil.copy2(os.getcwd() + '/recordings/' + i, os.getcwd() + '/filtered/' + i)
        return temp_list