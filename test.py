from xenocanto import create_dir, get_json
from urllib import request
import unittest
import shutil, os

class TestCases(unittest.TestCase):
    # Check if connection to the API can be established through arbitrary query (chosen for speed)
    def test_query_connection(self):
        status = request.urlopen('https://www.xeno-canto.org/api/2/recordings?query=cnt:any').getcode()
        self.assertEqual(status, 200)


    # Check if all JSON files for all pages are being saved
    def test_get_json(self):
        get_json(['gen:Otis'])
        self.assertTrue(os.path.exists(os.getcwd() + '/queries/gen|Otis/page1.json'))

    # Tear down test folders and files
    def tearDown(self):
        shutil.rmtree(os.getcwd() + '/queries/')
