# Simplify acquisition of recordings from xeno-canto.org based on desired criteria
from urllib import request
import json
import os


def get_recordings(list_in):
    if (os.path.isdir(os.getcwd() + '/queries')==False):
        os.mkdir(os.getcwd() + '/queries')
    if (os.path.isdir(os.getcwd() + '/recordings')==False):
        os.mkdir(os.getcwd() + '/recordings')
    url = 'https://www.xeno-canto.org/api/2/recordings?query='
    for i in range(0, len(list_in)):
        url += (list_in[i] + '%20')
    response = request.urlopen(url)
    data = response.read()
    data_json = json.loads(data.decode('utf-8'))
    query_info = open(os.getcwd() + '/queries/temp.txt', 'w+')
    json.dump(data_json, query_info)
    query_info.close()
    filename = url[50:-1]
    os.rename(os.getcwd() + '/queries/temp.txt', os.getcwd() + '/queries/' + (filename.replace('%20', '_')).replace('%2', '') + '.json')

    for i in range(0, len(data_json["recordings"])):
        cat_id = data_json["recordings"][i]["id"]
        if (os.path.isfile(os.getcwd() + '/recordings/' + (data_json["recordings"][i]["en"]).replace(' ', '_') + cat_id + '.mp3')) == False:
            download_url = 'https:' + data_json["recordings"][i]["file"]
            mp3 = open(os.getcwd() + '/recordings/temp.mp3', 'wb')
            dl = request.urlopen(download_url)
            data = dl.read()
            mp3.write(data)
            mp3.close()
            os.rename(os.getcwd() + '/recordings/temp.mp3', os.getcwd() + '/recordings/' + (data_json["recordings"][i]["en"]).replace(' ', '_') + cat_id + '.mp3')
