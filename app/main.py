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
A production version of this would be better with:
- gunicorn/uwsgi
- the Flask API module
- proper Bearer tokens and JWTs
- Webhooks and Status endpoints broken into Classes and separated into modules
- add reqparse for sanitizing inputs
- an API management interface for token and job management
- bcrypting the stored auth tokens
- a better datastore
- a swagger doc

    :copyright: (c) 2020 by Jeff Sutch
    :license: BSD 2.0, see LICENSE_FILE for more details.
"""
# fix the supervisor start error
import sys
sys.path.append('/usr/local/lib/python3.8/site-packages')
sys.path.append('/var/www/webhook/app')
sys.path.append('.')

# web stuff
from flask import Flask, request, Response, jsonify, abort
from flask_restful import Resource, reqparse
import requests
from datetime import datetime, timedelta
import os, sys, binascii, uuid, random, logging, json

# logging setup
logging.basicConfig(filename='/var/www/webhook/app/app.log',level=logging.WARN)

# temp prototyping db
import sqlitedict
sqlitedict.PICKLE_PROTOCOL = 4 #try to overcome the HIGHEST PICKLE problem for different platforms
from sqlitedict import SqliteDict
jobsdb = SqliteDict('/var/www/webhook/app/jobs.db', autocommit=True)
tokensdb = SqliteDict('/var/www/webhook/app/tokens.db', autocommit=True)
sessionsdb = SqliteDict('/var/www/webhook/app/sessions.db', autocommit=True)


# TLS Context Config (need to have a certs in the paths)
# comment out if not using TLS
# import ssl
# context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
# context.load_cert_chain('/var/www/webhook/app/certs/fullchain.pem', '/var/www/webhook/app/certs/privkey.pem')

# add flask secret_key to a file named 'creds.py' as 'secret_key'='MySecretKey'
# make sure that the local dir is imported into PYTHONPATH
sys.path.append(".")
import creds 
import tokens_initialize

__author__ = "Jeff Sutch"
__copyright__ = "Copyright 2020, Collett Park Networks"
__credits__ = ["Jeff Sutch"]
__license__ = "GPL"
__version__ = "0.1.5"
__maintainer__ = "Jeff Sutch"
__email__ = "jeff@collettpark.com"
__status__ = "Demo"


# preparing to update this to formal flask app/api
app = Flask(__name__)
app.secret_key = creds.secret_key
# api = Api(app)

# create tokensdb with demo users before the app starts
# comment this out to use in production
@app.before_first_request
def add_users():
    """
    prepopulated demo users into tokensdb. this should be removed before deployment
    TODO:
    - update with persistent datastore not in git
    """
    tokens_initialize.create_all()

# sessions timeout
CLIENT_AUTH_TIMEOUT = 24

# Helper functions
def timeNow():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")

def response_uuid():
    return str(uuid.uuid4())

def temp_token():
    temp_token = binascii.hexlify(os.urandom(24))
    return temp_token.decode('utf-8')

def validUser(id):
    return True if id in tokensdb.keys() else False

def json_validator(data):
    try:
        json.loads(data)
        return True
    except Exception as e:
        return False


#
@app.route('/webhook', methods=['GET','POST'])
def webhooks():
    '''
    GET is a target to test credentials and refresh token timeout
    POST is the main webhook logic
    TODO:
    - rewrite to return Exceptions with tenacity backoffs
    '''
    try:
        json_validator(request.get_json())
    except Exception as e:
        print(e)
        return jsonify({'message':'request type must be JSON','status':'failed'}), 422 

    if request.method == 'GET':
        # Set session id
        _id = response_uuid()
        rq = request.get_json()
        clientId = rq['client_id']
        verify_token = rq['verify_token']
        print(clientId, verify_token)
        # 
        
        if (validUser(clientId) and tokensdb[clientId] == verify_token):
            sessionsdb[clientId] = {'ip':request.remote_addr, 'updatedAt': datetime.now(),'sessionId':_id}
            app.logger.info('token from from %s at %s', rq['client_id'], request.remote_addr)
            return jsonify({'status':'success'}), 200
        else:
            return jsonify({'status':'bad credentials'}), 401


    elif request.method == 'POST':
        # Set session id
        _id = response_uuid()
        print(request.get_json())
        # evaluate tokens and json
        rq = request.get_json()
        clientId = rq['client_id']
        verify_token = rq['verify_token']
        clientService = rq['service']
        clientIp = request.remote_addr
        #print(request.data)
        #print(verify_token)

        # verify tokens
        if validUser(clientId) and tokensdb[clientId] == verify_token:
            sessionsdb[clientId] = {'ip':request.remote_addr, 'updatedAt': datetime.now(),'sessionId':_id}
            app.logger.info('token from from %s at %s', rq['client_id'], request.remote_addr)
        else:
            return jsonify({'status':'bad credentials'}), 401


        # check for client session
        # if client in sessionsdb:
        if clientId in sessionsdb:
            if datetime.now() - sessionsdb[clientId]['updatedAt'] > timedelta(hours=CLIENT_AUTH_TIMEOUT):
                app.logger.info('stale token from from %s at %s', rq['client_id'], request.remote_addr)
                sessionsdb.pop(clientId)
                return jsonify({'status':'authorization timeout'}), 401
            else:
                app.logger.info('accepted token from from %s at %s', clientId, request.remote_addr)
                print(request.json)
                # set session id and job id
                _jobId = response_uuid()
                # internal
                reqId = _id # each API call gets a request ID - UUID4
                jobId = _jobId # each job gets a job id - UUID4
                createdAt = timeNow() # when the request was created - datetime
                updatedAt = timeNow() # last updated time - datetime
                status = 'accepted' # did we accept or reject the initial call
                notified = 'no' # preset notify vars
                notifyoutput = 'not started'

                # assign variables from client data
                rq = request.get_json() # the incoming request
                clientCallback = rq['callback'] # where are we sending the callback - url/string 
                clientHeaders = rq['headers'] # get job headers
                clientData = rq['data'] # data package - json
                clientHeaders = rq['headers']
                clientMethodType = rq['methodtype']

                # log request
                app.logger.info('job %s accepted from %s at %s', jobId, clientId, request.remote_addr)

                # construct query and update the jobs database
                app.logger.info('writing job %s to database at %s', jobId, request.remote_addr)
                jobsdb[jobId] = {'clientId':clientId,'service':clientService, 'createTime':createdAt,'lastUpdate':updatedAt,'headers':clientHeaders,'methodtype': clientMethodType, 'data':clientData,'status':'accepted','requestId':reqId, 'callback': clientCallback, 'jobId': jobId, 'notified': notified, 'notifyoutput':notifyoutput}
                jobsdb.commit()
                app.logger.info('committed job %s to database at %s', jobId, request.remote_addr)

                returnString = {'job_id':jobId,'created':createdAt, 'status':'accepted'}
                return jsonify(returnString), 202
        else:
            return jsonify({'status':'not authorized'}), 401

    else:
        abort(400)


@app.route('/status', methods=['GET'])
def jobstatus():
    """
    accepts a job Id and returns the job status
    """
    try:
        json_validator(request.get_json())
    except Exception as e:
        print(e)
        return jsonify({'message':'request type must be JSON','status':'failed'}), 422 

    if request.method == 'GET':
        # Set session id
        _id = response_uuid()
        # get data
        rq = request.get_json()
        clientId = rq['client_id']
        verify_token = rq['verify_token']
        # print(clientId, verify_token)

        if (validUser(clientId) and tokensdb[clientId] == verify_token):
            sessionsdb[clientId] = {'ip':request.remote_addr, 'updatedAt': datetime.now(),'sessionId':_id}
            app.logger.info('/status token from from %s at %s', rq['client_id'], request.remote_addr)
        else:
            return jsonify({'status':'bad credentials'}), 401

        # Job ID
        jobId = rq['job_id']
        #items to be returned
        returnItems = ['jobId', 'lastUpdate', 'service', 'status', 'output', 'notified','notifyoutput']
        # do the lookup
        if jobId in jobsdb:
            job = jobsdb[jobId]
            returnStatus = {k:str(v) for k,v in job.items() if k in returnItems}
            # print(returnStatus)
            return jsonify(returnStatus),200
        else:
            return jsonify({"status":"No job with that ID exists"}), 404
    # else:
    #     abort(400)

if __name__ == '__main__':
    # without TLS
    app.run(host='0.0.0.0',port=6666, debug=True)
    # with TLS - need to uncomment the context head in imports
    # app.run(host='0.0.0.0',port=6666, debug=True, ssl_context=context)
