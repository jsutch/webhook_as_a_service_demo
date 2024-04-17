from .db import db
from datetime import datetime
from flask_bcrypt import generate_password_hash, check_password_hash

# https://docs.mongoengine.org/guide/defining-documents.html

# "{'added_by', 'verify_token', 'callback', 'methodtype', 'service', 'data', 'client_id', 'headers'}"
class Jobs(db.Document):
    """
    Handles all the job data
    """
    # jobId = db.UUIDField(required=True, unique=True)
    added_by = db.ReferenceField('User')
    status = db.StringField(required=True, max_length=16)
    notified = db.StringField(required=True, max_length=16)
    # sessionId = db.UUIDField(required=True, unique=True) #handled by jwt
    createdAt = db.DateTimeField(required=True, default=datetime.now)
    updatedAt = db.DateTimeField(required=True, default=datetime.now)
    output = db.StringField(required=False)
    notifyoutput = db.StringField(required=False)
    # job data
    service = db.URLField(required=True)
    callback = db.URLField(required=True)
    headers = db.DictField(required=True)
    methodtype = db.StringField(required=True,max_length=16)
    data = db.DictField(required=True)


class User(db.Document):
    """
    Handles all the user/client data
    """
    email = db.EmailField(required=True, unique=True)
    clientId =  db.StringField(required=True)
    password = db.StringField(required=True, min_length=16)
    # token = db.StringField(required=True, min_length=32, unique=True) # handled by jwt
    jobs = db.ListField(db.ReferenceField('Jobs', reverse_delete_rule=db.PULL))

    def hash_password(self):
        self.password = generate_password_hash(self.password).decode('utf8')

    def hash_token(self):
        self.token = generate_password_hash(self.token).decode('utf8')

    def check_password(self, password):
       return check_password_hash(self.password, password)

class Sessions(db.Document):
    """
    possibly not needed for flask sessions
    """
    jobId = db.StringField(required=True, unique=True)
    sessionId = db.StringField(required=True, unique=True)
    clientId =  db.EmailField(required=True)
    createdAt = db.DateTimeField(required=True, default=datetime.now)
    updatedAt = db.DateTimeField(required=True, default=datetime.now)