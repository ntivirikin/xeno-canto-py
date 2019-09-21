from xenocanto import metadata
from urllib import request
import unittest
import shutil
import os


class TestCases(unittest.TestCase):
    # Check if connection to the API can be established
    def test_conn(self):
        url = 'https://www.xeno-canto.org/api/2/recordings?query=cnt:any'
        status = request.urlopen(url).getcode()
        self.assertEqual(status, 200)

    def test_metadata(self):
        metadata(['Bearded Bellbird', 'q:A'])
        self.assertTrue(os.path.exists('dataset/metadata/BeardedBellbird&q_A/page1.json'))

    def tearDown(self):
        try:
            shutil.rmtree('dataset/')
        except OSError:
            pass
