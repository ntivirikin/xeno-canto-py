from urllib import request, error
import json, os, errno


# Creates directory if it does not exist
def create_dir(directory):
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


# Downloads all recordings based on search criteria
def get_recordings(search):

    # Initial query to determine number of pages and file name
    create_dir(os.getcwd() + '/queries')
    create_dir(os.getcwd() + '/recordings')
    url = 'https://www.xeno-canto.org/api/2/recordings?query='
    for val in search:
        url += val + '%20'
    try:
        r = request.urlopen(url)
    except error.HTTPError:
        errmsg = 'Error: 404! ' + url + ' does not exist!'
        create_dir(os.getcwd() + '/log/')
        errlog = open(os.getcwd() + '/log/connect_err.txt')
        errlog.write(errmsg + "\n")
        errlog.close()
        print(errmsg)
    data = r.read()
    data_json = json.loads(data.decode('utf-8'))

    # Name of query folder will be the inputted search criteria
    name = ((url[50:-1]).replace('%20', '_')).replace('%2', '')
    create_dir(os.getcwd() + '/queries/' + name)

    # Retrieve queries as .json files for all pages
    pages = data_json["numPages"]
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

        # Query files saved under related folder and named after page number
        os.rename(os.getcwd() + '/queries/' + name + '/temp.txt', os.getcwd() + '/queries/' + name + '/page' + str(i) + '.json')

        # Retrieve recordings as .mp3 files from current page
        for k in range(0, len(data_json["recordings"])):
            
            # Recording name will be the English name tag value and recording id
            rec_name = (data_json["recordings"][k]["en"]).replace(' ', '') + data_json["recordings"][k]["id"]
            if (os.path.isfile(os.getcwd() + '/recordings/' + rec_name + '.mp3')) == False:
                download_url = 'https:' + data_json["recordings"][k]["file"]
                try:
                    dl = request.urlopen(download_url)
                except error.HTTPError:
                    errmsg = (data_json["recordings"][k]["en"]).replace(' ', '') + data_json["recordings"][k]["id"] + ' could not be found at: ' + download_url
                    create_dir(os.getcwd() + '/log/')
                    errlog = open(os.getcwd() + '/log/download_err.txt')
                    errlog.write(errmsg + "\n")
                    errlog.close()
                    print(errmsg)
                    continue
                data = dl.read()
                mp3 = open(os.getcwd() + '/recordings/temp.mp3', 'wb')
                mp3.write(data)
                mp3.close()
                os.rename(os.getcwd() + '/recordings/temp.mp3', os.getcwd() + '/recordings/' + rec_name + '.mp3')
