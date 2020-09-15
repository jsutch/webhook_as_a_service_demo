#!/usr/bin/env python3

import unittest
import json

from main import app
# from tests.BaseTest import BaseTest

class SignupTest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_auth_success(self):
        payload = json.dumps({
            "email": "66666666666668",
            "password": "d7811aa4852d7c021df3da133f8d3e11ad1e5c42d3ed0a1a"
        })
        # send request
        response = self.app.get('/webhook', headers={"Content-Type": "application/json"}, data=payload)
        # test response
        self.assertEqual(str, type(response.json['status']))
        self.assertEqual(200, response.status_code)
