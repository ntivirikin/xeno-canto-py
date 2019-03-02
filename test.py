import unittest
from urllib import request
from xenocanto import get_recordings
import os

class TestCases(unittest.TestCase):
    # Check if connection to the API can be established through arbitrary query (chosen for speed)
    def test_query_connection(self):
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
        self.assertTrue(os.path.isfile(os.getcwd() + '/queries/gen:rhea_cnt:Brazil/page1.json'))
