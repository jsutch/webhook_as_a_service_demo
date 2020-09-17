import sys
sys.path.append('/usr/local/lib/python3.8/site-packages')
sys.path.append('/var/www/webhook/app')
sys.path.append('.')

# web stuff
# from flask import Flask, request, Response, jsonify, abort
from flask_restful import Resource, reqparse
from datetime import datetime, timedelta
import os, sys, binascii, uuid, random, logging, json


from flask import Response, request
from flask_jwt_extended import jwt_required
from database.models import Jobs, User, Sessions
from flask_restful import Resource
from mongoengine.errors import FieldDoesNotExist, \
NotUniqueError, DoesNotExist, ValidationError, InvalidQueryError
from resources.errors import SchemaValidationError, MovieAlreadyExistsError, \
InternalServerError, UpdatingMovieError, DeletingMovieError, MovieNotExistsError


# logging setup
logging.basicConfig(filename='/var/www/webhook/app/app.log',level=logging.WARN)



__author__ = "Jeff Sutch"
__copyright__ = "Copyright 2020, Collett Park Networks"
__credits__ = ["Jeff Sutch"]
__license__ = "GPL"
__version__ = "0.2.1"
__maintainer__ = "Jeff Sutch"
__email__ = "jeff@collettpark.com"
__status__ = "Demo"


@app.route('/jobmanager', methods=['GET'])
def validate():
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

   # Set session id
    _id = response_uuid()
    rq = request.get_json()
    clientId = rq['client_id']
    verify_token = rq['verify_token']
    print(clientId, verify_token)

   
@app.route('/jobmanager', methods=['POST'])
def add_job():
    '''
    POST is the main webhook logic
    TODO:
    - rewrite to return Exceptions with tenacity backoffs
    '''
    try:
        json_validator(request.get_json())
    except Exception as e:
        print(e)
        return jsonify({'message':'request type must be JSON','status':'failed'}), 422 

    if (validUser(clientId) and tokensdb[clientId] == verify_token):
                sessionsdb[clientId] = {'ip':request.remote_addr, 'updatedAt': datetime.now(),'sessionId':_id}
                app.logger.info('token from from %s at %s', rq['client_id'], request.remote_addr)
                return jsonify({'status':'success'}), 200
    else:
            return jsonify({'status':'bad credentials'}), 401
    # Set session id
    _id = response_uuid()
    # evaluate tokens and json
    rq = request.get_json()
    clientId = rq['client_id']
    verify_token = rq['verify_token']
    clientService = rq['service']
    clientIp = request.remote_addr
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
            app.logger.info('committed job %s to database at %s', jobId, request.remote_addr)
            returnString = {'job_id':jobId,'created':createdAt, 'status':'accepted'}
            return jsonify(returnString), 202
    else:
        return jsonify({'status':'not authorized'}), 401



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



class WebhookApi(Resource):
    def get(self):
        movies = Movie.objects().to_json()
        return Response(movies, mimetype="application/json", status=200)

    def post(self):
        body = request.get_json()
        movie =  Movie(**body).save()
        id = movie.id
        return {'id': str(id)}, 200
        

class StatusApi(Resource):
    def get(self, id):
        movies = Movie.objects.get(id=id).to_json()
        return Response(movies, mimetype="application/json", status=200)