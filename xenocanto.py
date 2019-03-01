from urllib import request
import json, os, errno

def create_dir(directory):
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def get_recordings(search):
    create_dir(os.getcwd() + '/queries')
    create_dir(os.getcwd() + '/recordings')
    url = 'https://www.xeno-canto.org/api/2/recordings?query='
    for val in search:
        url += val + '%20'
    r = request.urlopen(url)
    data = r.read()
    data_json = json.loads(data.decode('utf-8'))
    pages = data_json["numPages"]
    name = ((url[50:-1]).replace('%20', '_')).replace('%2', '')
    create_dir(os.getcwd() + '/queries/' + name)

    for i in range(1, pages + 1):
        url = 'https://www.xeno-canto.org/api/2/recordings?query='
        for val in search:
            url += val + '%20'
        url += '&page=' + str(i)
        r = request.urlopen(url)
        data = r.read()
        data_json = json.loads(data.decode('utf-8'))
        query_info = open(os.getcwd() + '/queries/' + name + '/temp.txt', 'w+')
        json.dump(data_json, query_info)
        query_info.close()
        os.rename(os.getcwd() + '/queries/' + name + '/temp.txt', os.getcwd() + '/queries/' + name + '/page' + str(i) + '.json')

        for k in range(0, len(data_json["recordings"])):
            rec_name = (data_json["recordings"][k]["en"]).replace(' ', '') + data_json["recordings"][k]["id"]
            if (os.path.isfile(os.getcwd() + '/recordings/' + rec_name + '.mp3')) == False:
                download_url = 'https:' + data_json["recordings"][k]["file"]
                mp3 = open(os.getcwd() + '/recordings/temp.mp3', 'wb')
                dl = request.urlopen(download_url)
                data = dl.read()
                mp3.write(data)
                mp3.close()
                os.rename(os.getcwd() + '/recordings/temp.mp3', os.getcwd() + '/recordings/' + rec_name + '.mp3')
