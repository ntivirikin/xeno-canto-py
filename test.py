import unittest
from urllib import request
from xenocanto import get_recordings, create_dir
import os
import shutil

class TestCases(unittest.TestCase):

    # Check if connection to the API can be established through arbitrary query (chosen for speed)
    def test_query_connection(self):
        create_dir(os.getcwd() + '/queries/')
        create_dir(os.getcwd() + '/recordings/')
        status = request.urlopen('https://www.xeno-canto.org/api/2/recordings?query=cnt:any').getcode()
        self.assertEqual(status, 200)


    # Check if query can be made with one piece of criteria
    def test_query_single(self):
        get_recordings(['gen:Otis'])
        self.assertTrue(os.path.isfile(os.getcwd() + '/queries/gen:Otis/page1.json'))
        self.assertTrue(os.path.isfile(os.getcwd() + '/recordings/GreatBustard459281.mp3'))
        

    # Check if query can be made with multiple criteria
    def test_query_multiple(self):
        get_recordings(['gen:rhea', 'cnt:Brazil'])
        result = len([1 for x in list(os.scandir(os.getcwd() + '/recordings/')) if x.is_file()])
        self.assertTrue(os.path.isfile(os.getcwd() + '/queries/gen:rhea_cnt:Brazil/page1.json'))
        self.assertEqual(result, 10)


    def test_filter_quality(self):
        get_recordings(['gen:rhea', 'cnt:Brazil'])
        filter_quality('/queries/gen:rhea_cnt:Brazil', 'B')
        self.assertTrue(os.path.exists(os.getcwd() + '/filtered/'))
        self.assertEqual


    # Remove testing directories
    def tearDown(self):
        shutil.rmtree(os.getcwd() + '/queries/')
        shutil.rmtree(os.getcwd() + '/recordings/')
