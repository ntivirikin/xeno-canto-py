from xenocanto import err_log, create_dir, get_json, get_mp3, get_rec
from urllib import request
import unittest
import shutil
import os


class TestCases(unittest.TestCase):
    # Check if connection to the API can be established
    def test_query_connection(self):
        url = 'https://www.xeno-canto.org/api/2/recordings?query=cnt:any'
        status = request.urlopen(url).getcode()
        self.assertEqual(status, 200)

    # Check if get_json retrieves JSON file
    def test_get_json(self):
        get_json(['gen:Otis'])
        self.assertTrue(os.path.exists(os.getcwd() +
                        '/queries/gen|Otis/page1.json'))

    # Check if get_mp3 retrieves MP3 file(s) based  on list of JSON file
    # paths from get_json
    def test_get_mp3(self):
        get_mp3(get_json(['gen:Otis']))
        self.assertTrue(os.getcwd() + '/recordings/GreatBustard459281.mp3')

    # Check if get_rec retrieves JSON and MP3 for a single search criterion
    def test_get_rec_single(self):
        get_rec(['gen:Otis'])
        self.assertTrue(os.path.exists(os.getcwd() +
                        '/queries/gen|Otis/page1.json'))
        self.assertTrue(os.path.exists(os.getcwd() +
                        '/recordings/GreatBustard459281.mp3'))

    # Check if get_rec retrieves JSON and MP3 for multiple search criteria
    def test_get_rec_multiple(self):
        get_rec(['gen:Larus', 'q:A', 'cnt:Sweden'])
        self.assertTrue(os.path.exists(os.getcwd() +
                        '/queries/gen|Larus_q|A_cnt|Sweden/page1.json'))
        DIR = os.getcwd() + '/recordings/'
        result = len([name for name in os.listdir(DIR)
                     if os.path.isfile(os.path.join(DIR, name))])
        self.assertEqual(result, 28)

    # Remove folders used for testing
    def tearDown(self):
        try:
            shutil.rmtree(os.getcwd() + '/queries/')
            shutil.rmtree(os.getcwd() + '/recordings/')
        except FileNotFoundError:
            pass
