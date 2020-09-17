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
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.models import Jobs, User, Sessions
from flask_restful import Resource
from mongoengine.errors import FieldDoesNotExist, \
NotUniqueError, DoesNotExist, ValidationError, InvalidQueryError
from resources.errors import SchemaValidationError, JobAlreadyExistsError, \
InternalServerError, UpdatingJobError, DeletingJobError, JobNotExistsError


# logging setup
# logging.basicConfig(filename='/var/www/webhook/app/app.log',level=logging.WARN)



__author__ = "Jeff Sutch"
__copyright__ = "Copyright 2020, Collett Park Networks"
__credits__ = ["Jeff Sutch"]
__license__ = "GPL"
__version__ = "0.2.1"
__maintainer__ = "Jeff Sutch"
__email__ = "jeff@collettpark.com"
__status__ = "Demo"




class JobsApi(Resource):
    """
    put jobs into the queue, test token
    """
    @jwt_required
    def post(self):
        '''
        POST is the main webhook logic
        TODO:
        - rewrite to return Exceptions with tenacity backoffs
        '''
        try:
            user_id = get_jwt_identity()
            body = request.get_json()
            user = User.objects.get(id=user_id)
            job =  Jobs(**body, added_by=user)
            job.status = 'accepted'
            job.notified = 'no'
            job.save()
            user.update(push__jobs=job)
            user.save()
            id = job.id
            return {'id': str(id)}, 200
        except (FieldDoesNotExist, ValidationError):
            raise SchemaValidationError
        except NotUniqueError:
            raise JobAlreadyExistsError
        except Exception as e:
            raise InternalServerError

    def get():
        '''
        GET is a target to test credentials and refresh token timeout
        '''
        def get(self):
            movies = Job.objects().to_json()
            return Response(movies, mimetype="application/json", status=200)

 
class StatusApi(Resource):
    def get(self, id):
        try:
            jobs = Jobs.objects.get(id=id).to_json()
            return Response(jobs, mimetype="application/json", status=200)
        except DoesNotExist:
            raise JobNotExistsError
        except Exception:
            raise InternalServerError

