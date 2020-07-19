from xenocanto import metadata, download, gen_meta, purge, delete
from urllib import request
import unittest
import shutil
import os


# TODO: 
#   [ ] Mock objects and test calls
#   [ ] Test resuming a download after interrupt
class TestCases(unittest.TestCase):


    # Check if connection to the API can be established
    def test_conn(self):
        url = 'https://www.xeno-canto.org/api/2/recordings?query=cnt:any'
        status = request.urlopen(url).getcode()
        self.assertEqual(status, 200)


    # Checks if metadata is successfully downloaded into the expected folder structure
    def test_metadata(self):
        metadata(['Bearded Bellbird', 'q:A'])
        self.assertTrue(os.path.exists('dataset/metadata/BeardedBellbird&q_A/page1.json'))


    # Checks if audio files are downloaded into the correct directory
    def test_download(self):
        download(['gen:Otis'])
        self.assertTrue(os.path.exists('dataset/metadata/gen_Otis/page1.json'))
        self.assertTrue(os.path.exists('dataset/audio/GreatBustard/459281.mp3'))


    # Check if purge is deleting folders based on file count
    def test_purge(self):
        download(['gen:Otis'])
        download(['Bearded Bellbird', 'q:A', 'cnt:Brazil'])
        purge(7)
        self.assertFalse(os.path.exists('dataset/audio/GreatBustard/'))
        self.assertTrue(os.path.exists('dataset/audio/BeardedBellbird/'))

    
    # Check if metadata is being correctly generated for one
    # recording with metadata already saved
    def test_gen_meta_with_extra_metadata(self):
        metadata(['gen:Otis'])
        download(['Bearded Bellbird', 'q:A', 'cnt:Brazil'])
        gen_meta()
        self.assertTrue(os.path.exists('dataset/metadata/library.json'))


    # Check if deleting files using multiple filters
    def test_delete(self):
        download(['Bearded Bellbird', 'q:A', 'cnt:Brazil'])
        delete(['id:493159', 'id:427845'])
        self.assertFalse(os.path.exists('dataset/audio/BeardedBellbird/493159.mp3'))
        self.assertFalse(os.path.exists('dataset/audio/BeardedBellbird/427845.mp3'))


    # Check if deleting files from multiple folders
    def test_delete_multiple_species(self):
        download(['Bearded Bellbird', 'q:A', 'cnt:Brazil'])
        download(['gen:Otis'])
        delete(['id:493159', 'gen:Otis'])
        self.assertFalse(os.path.exists('dataset/audio/BeardedBellbird/493159.mp3'))
        self.assertFalse(os.path.exists('dataset/audio/GreatBustard/'))

    # Check if metadata is being correctly generated when some metadata is saved
    # and some must be retrieved from an API call
    def test_gen_meta_with_extra_tracks(self):
        path = metadata(['gen:Otis'])
        download(['gen:Otis'])
        download(['Bearded Bellbird', 'q:A', 'cnt:Brazil'])
        shutil.rmtree(path)
        gen_meta()
        self.assertTrue(os.path.exists('dataset/metadata/library.json'))

    
    # Removes files used in testing
    def tearDown(self):
        try:
            shutil.rmtree('dataset/')
        except OSError:
            pass
