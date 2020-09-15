import unittest

from app import app

class BaseTest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
