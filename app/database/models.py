from .db import db

# https://docs.mongoengine.org/guide/defining-documents.html

class Job(db.Document):
    """
    Handles all the job data
    """
    jobId = db.UUIDField(required=True, unique=True)
    status = db.StringField(required=True, max_length=16)
    notified = db.StringField(required=True, max_length=16)
    sessionId = db.UUIDField(required=True, unique=True)
    createdAt = db.DateTimeField(required=True, default=datetime.datetime.now)
    updatedAt = db.DateTimeField(required=True, default=datetime.datetime.now)
    output = db.StringField(required=True, unique=True)
    notifyoutput = db.StringField(required=True, unique=True)
    # job data
    clientCallback = db.URLField(required=True, unique=True)
    clientHeaders = db.StringField(required=True, unique=True)
    clientMethodType = db.StringField(required=True,max_length=16)
    clientData = db.DictField(required=True)


class User(db.Document):
    """
    Handles all the user/client data
    """
    email = db.EmailField(required=True, unique=True)
    clientId =  db.EmailField(required=True, unique=True)
    password = db.StringField(required=True, min_length=16)
    token = db.StringField(required=True, min_length=32, unique=True)

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
    createdAt = db.DateTimeField(required=True, default=datetime.datetime.now)
    updatedAt = db.DateTimeField(required=True, default=datetime.datetime.now)