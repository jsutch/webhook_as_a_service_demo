#!/usr/bin/env python3
import unittest
import json

from main import app


class JobTest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
    def test_job_success(self):
        payload = json.dumps({
            "client_id": "66666666666668",
            "service": "http://snout:7777/service",
            "methodtype":"POST",
            "headers":  {"serviceAuthId":"successfulcorp","serviceAuthToken":"rjc9uBixhWZ2l52mEMViGJfyQh5QfL6wAeuuCl0AsB4=","user-agent": "successfulApp/0.1.2","Content-Type":"application/json"},
            "callback": "http://snout:7777/callback",
            "data": {"userId": 1,"id": 5,"title": "laboriosam mollitia et enim quasi adipisci quia provident illum","completed": false},
            "verify_token":"d7811aa4852d7c021df3da133f8d3e11ad1e5c42d3ed0a1a"
            })
        # send request
        response = self.app.post('/webhook', headers={"Content-Type": "application/json"}, data=payload)
        # test response
        self.assertEqual(str, type(response.json['status']))
        self.assertEqual(str, type(response.json['job_id']))
        self.assertEqual(str, type(response.json['created']))
        self.assertEqual(200, response.status_code)