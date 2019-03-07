from urllib import request
import json, os, errno, error, shutil

#TODO: Combine filter with get_recordings?


def err_log(errno):
    errmsg = 'Error: ' + errno + ' Please view the error log for more details.'
    errlog = open(os.getcwd() + '/error_log.txt')
    errlog.write(errmsg + '\n')
    errlog.close()
    print(errmsg)


# Creates directory if it does not exist
def create_dir(directory):
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            errmsg = 'Error: ' + e.errno + ' Please view the error log for more details.'
            err_log(errmsg)
            raise


# Creates a URL based on user given criteria and whether pages are being scanned
def url_builder(criteria, pages = None):
    url = 'https://www.xeno-canto.org/api/2/recordings?query='
    url_list = []
    for val in criteria:
        url += val + ' '
    if pages != None:
        for i in range(1, pages):
            url_temp += '&page=' + i
            url_list.append(url_temp)
            return url_list
    else:
        return url


# Open and retrieve JSON data from a URL
def read_url(url):
    try:
        r = request.urlopen(url)
    except error.HTTPError as e:
        err_log(e.errno)
    return r.read()


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
    url = url_builder(background)
    data = read_url(url)
    data_json = json.loads(data.decode('utf-8'))

    # Retrieve queries as .json files for all pages
    num_pages = data_json["numPages"]
    temp_list = []

    for i in url_builder(background, pages = num_pages):
        read_url(i)
        data_json = json.loads(data)
        
        for i in range(0, len(data_json["recordings"])):
            temp_list.append((data_json["recordings"][i]["en"]).replace(' ', '') + data_json["recordings"][i]["id"] + '.mp3')
        data_json.close()

    for i in temp_list:
        shutil.copy2(os.getcwd() + '/recordings/' + i, os.getcwd() + '/filtered/' + i)
    return temp_list


# Downloads all recordings based on search criteria
def get_recordings(search):

    # Initial query to determine number of pages and file name
    create_dir(os.getcwd() + '/queries')
    create_dir(os.getcwd() + '/recordings')
    
    url = url_builder(search)
    data = read_url(url)
    data_json = json.loads(data.decode('utf-8'))

    # Name of query folder will be the inputted search criteria
    name = ((url[50:-1]).replace('%20', '_')).replace('%2', '')
    create_dir(os.getcwd() + '/queries/' + name)

    # Retrieve queries as .json files for all pages
    num_pages = data_json["numPages"]


    for i in url_builder(search, pages = num_pages):
        read_url(i)
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

                read_url(download_url)

                mp3 = open(os.getcwd() + '/recordings/temp.mp3', 'wb')
                mp3.write(data)
                mp3.close()
                os.rename(os.getcwd() + '/recordings/temp.mp3', os.getcwd() + '/recordings/' + rec_name + '.mp3')
