# Simplify acquisition of recordings from xeno-canto.org based on desired criteria
import json
import os
from urllib import request

# Grab recording based on catalog number range (or singele)
def get_by_id(start=None, end=None):
    if (end==None):
        url = 'https://www.xeno-canto.org/api/2/recordings?query=nr:' + str(start)
    else:
        url = 'https://www.xeno-canto.org/api/2/recordings?query=nr:' + str(start) + '-' + str(end)
    
    response = request.urlopen(url)
    data = response.read()
    data_json = json.loads(data.decode('utf-8'))
    result = []

    for i in range(0, len(data_json["recordings"])):
        download_url = 'https:' + data_json["recordings"][i]["file"]
        mp3 = open('temp.mp3', 'wb')
        dl = request.urlopen(download_url)
        data = dl.read()
        mp3.write(data)
        mp3.close()
        cat_id = data_json["recordings"][i]["id"]
        result.append(cat_id)
        os.rename('temp.mp3', (data_json["recordings"][i]["en"]).replace(' ', '_') + cat_id + '.mp3')
    return result
