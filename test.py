from xenocanto import err_log, create_dir, get_json, get_mp3, get_rec
from urllib import request
import unittest
import shutil, os

class TestCases(unittest.TestCase):
    # Check if connection to the API can be established through arbitrary query (chosen for speed)
    def test_query_connection(self):
        status = request.urlopen('https://www.xeno-canto.org/api/2/recordings?query=cnt:any').getcode()
        self.assertEqual(status, 200)


    # Check if JSON retrieval is working
    def test_get_json(self):
        get_json(['gen:Otis'])
        self.assertTrue(os.path.exists(os.getcwd() + '/queries/gen|Otis/page1.json'))


    # Check if mp3 retrieval from JSON is working
    def test_get_mp3(self):
        get_mp3(get_json(['gen:Otis']))
        self.assertTrue(os.getcwd() + '/recordings/GreatBustard459281.mp3')


    # Check if get_rec retrieves JSON and mp3
    def test_get_rec(self):
        get_rec(['gen:Otis'])
        self.assertTrue(os.path.exists(os.getcwd() + '/queries/gen|Otis/page1.json'))
        self.assertTrue(os.getcwd() + '/recordings/GreatBustard459281.mp3')


    # Remove folders used for testing
    def tearDown(self):
        try:
            shutil.rmtree(os.getcwd() + '/queries/')
            shutil.rmtree(os.getcwd() + '/recordings/')
        except FileNotFoundError:
            pass