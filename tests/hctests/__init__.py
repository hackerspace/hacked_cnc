import os
import sys
import shutil
try:
    import unittest2 as unittest
except ImportError:
    import unittest

cpath = os.path.dirname(os.path.realpath(__file__))
# alter path so we can import hc
hc_path = os.path.abspath(os.path.join(cpath, "../.."))
sys.path.insert(0, hc_path)
os.environ["PATH"] = "{0}:{1}".format(hc_path, os.environ["PATH"])

# use separate config file for tests
os.environ["HC_CONFIG_FILE"] = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "test_config.conf")

# create temporary directory for the tests
TEST_DIR = "/tmp/hc_test_data"
if os.path.exists(TEST_DIR):
    shutil.rmtree(TEST_DIR)
os.makedirs(TEST_DIR)


class TestCase(unittest.TestCase):
    """
    Class that initializes required configuration variables.
    """

    @classmethod
    def tearDownClass(cls):
        """
        Remove temporary directory.
        """

        shutil.rmtree(TEST_DIR)

def main():
    unittest.main()
