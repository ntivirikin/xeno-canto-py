import unittest
from urllib import request
from xenocanto import get_by_id
import os

class TestCases(unittest.TestCase):
    # Check if connection to the API can be established through arbitrary query (chosen for speed)
    def test_query_connection(self):
        status = request.urlopen('https://www.xeno-canto.org/api/2/recordings?query=cnt:any').getcode()
        self.assertEqual(status, 200)

    
    # Check if file was retrieved with correct catalog number
    def test_single_get_by_id(self):
        cat_id = get_by_id(438595)
        self.assertTrue(os.path.isfile('Blue_Jay438595.mp3'))
        self.assertEqual(cat_id, ['438595'])


    # Check if files falling in the catalog number range provided have been downloaded with correct catalog numbers
    def test_range_get_by_id(self):
        cat_id = get_by_id(438595, 438596)
        self.assertTrue(os.path.isfile('Blue_Jay438595.mp3'))
        self.assertTrue(os.path.isfile('Kamchatka_Leaf_Warbler438596.mp3'))
        self.assertEquals(cat_id[0], '438595')
        self.assertEquals(cat_id[1], '438596')