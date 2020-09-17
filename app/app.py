# -*- coding: utf-8 -*-
"""
simple Webhook As A Service flask API frontend. 

There are two endpoints with three methods (swagger doc attached):
/webhook GET - tests simple authentication and refreshes a session in a sessiondb
/webhook POST - does simple authentication and accepts a job package (header and data package) to pass off to an API runner. Creates an entry in the jobsdb which will be picked up by the worker. Returns the id to the client.

/status GET - takes authentication tokens and a jobid, returns the current status of the job from the jobsdb


WebHook As A Service broker
- This project will be to build a "Webhook-as-a-Service" microservice. The microservice should be a Flask app that exposes a simple API which can:
- Receive a POST request with information on the webhook the service should send (headers, request type, POST body, URL params, etc)
- Return back an "id" for the webhook that will be sent, so the client can query the API later to see the status of the webhook (sent, failed, retrying, etc)
- Implement retry logic, so that the webhook will be retried with an exponential backoff if the webhook URL responds with a bad status code (non-200)

TODO Notes:


    :copyright: (c) 2020 by Jeff Sutch
    :license: BSD 2.0, see LICENSE_FILE for more details.
"""
# fix the supervisor start error
import sys
sys.path.append('/usr/local/lib/python3.8/site-packages')
sys.path.append('/var/www/webhook/app')
sys.path.append('.')

# web stuff
from datetime import datetime, timedelta
import os, sys, binascii, uuid, random, logging, json

# Replacement chunks - sort this out
from flask import Flask
from flask_restful import Api
from resources.routes import initialize_routes

from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_mail import Mail 

# local imports
from database.db import initialize_db

# Errors
from resources.errors import errors

import creds 
# import tokens_initialize

# logging setup
logging.basicConfig(filename='/var/www/webhook/app/app.log',level=logging.INFO)

# TLS Context Config (need to have a certs in the paths)
# comment out if not using TLS
# import ssl
# context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
# context.load_cert_chain('/var/www/webhook/app/certs/fullchain.pem', '/var/www/webhook/app/certs/privkey.pem')




# preparing to update this to formal flask app/api
app = Flask(__name__)
app.secret_key = creds.secret_key
api = Api(app)


# import JWT key
app.config["JWT_SECRET_KEY"] = creds.JWT_SECRET_KEY

app.config["MONGODB_SETTINGS"] = {
    "db":'movie-bag',
    "username":creds.mongouser,
    "password":creds.mongopassword,
    "host":"mongodb://storage/webhook?authSource=admin",
}



initialize_db(app)
initialize_routes(api)

