from urllib import request, error
from datetime import datetime
import json, os, errno, shutil


# Prints error message to users
def err_log(error):
    date = str(datetime.utcnow())
    errmsg = '[' + date + '] ' + str(error.__name__) + ' occurred.'
    print(errmsg)


# Creates directory with error logging
def create_dir(directory):
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            err_log(e)
            raise


# Creates a URL based on user given criteria and whether pages are being scanned
def url_builder(criteria, pages = 0):
    url = 'https://www.xeno-canto.org/api/2/recordings?query='
    url_list = []
    for val in criteria:
        url += val + ' '
    if pages != 0:
        for i in range(1, pages + 1):
            url_temp = url + '&page=' + str(i)
            url_temp = url_temp.replace(' ', '')
            url_list.append(url_temp)
            return url_list
    else:
        return url


# Retrieve JSON based on search criteria
def get_json(search):
    url = url_builder(search)
    try:
        r = request.urlopen(url)
    except error.HTTPError as e:
        err_log(e)
        raise
    data = json.loads(r.read().decode('UTF-8'))
    
    # Creating folder name and replacing characters
    name = url[50:-1]
    for re in (('%20', '_'), ('%2', ''), (':', '|')):
        name = name.replace(*re)
    folder = os.getcwd() + '/queries/' + name
    create_dir(folder)

    # Saving JSON from all pages
    num_pages = data["numPages"]
    print(num_pages)
    temp_txt = folder + '/temp.txt'
    json_list = []
    page = 1
    for url in url_builder(search, num_pages):
        try:
            r = request.urlopen(url)
        except error.HTTPError as e:
            err_log(e)
            continue
        data = json.loads(r.read().decode('UTF-8'))
        txt = open(temp_txt, 'w+')
        json.dump(data, txt)
        txt.close()
        file_name = folder + '/page' + str(page) + '.json'
        os.rename(temp_txt, file_name)
        json_list.append(file_name)
        page += 1
    return json_list


def get_mp3(path):
    # Creating folder structure and reserving temp path
    folder = os.getcwd() + '/recordings/'
    mp3_list = []
    create_dir(folder)
    temp_mp3 = folder + 'temp.mp3'

    # Parsing all JSON files for download links and executing them
    for file in path:
        data = json.load(open(file))
        for i in range(0, len(data["recordings"])):
            rec_path = folder + (data["recordings"][i]["en"]).replace(' ', '') + data["recordings"][i]["id"] + '.mp3'
            if (os.path.exists(rec_path)) == False:
                url = 'https:' + data["recordings"][i]["file"]
                try:
                    r = request.urlopen(url)
                except error.HTTPError as e:
                    err_log(e)
                    continue
                data = r.read()
                mp3 = open(temp_mp3, 'wb')
                mp3.write(data)
                mp3.close
                os.rename(temp_mp3, rec_path)
                mp3_list.append(rec_path)
    return mp3_list


# Get recordings based on search term, returns lists of json and mp3 paths
def get_rec(search):
    json_list = get_json(search)
    mp3_list = get_mp3(json_list)
    return [json_list, mp3_list]