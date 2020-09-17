
Class Helpers(Resource):
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

    def testJson(data):
        """
        wrapper for json validator
        """
        try:
            json_validator(request.get_json())
        except Exception as e:
            print(e)
            return jsonify({'message':'request type must be JSON','status':'failed'}), 422 


class JobFunctions(Resource):
    def addJob(jobid, ):
        """
        update the database status for 'jobid' with 'status'
        TODO:
        - limit to known status types
        """

        db = SqliteDict('/var/www/webhook/app/jobs.db', autocommit=True)
        with db:
            munger = db[jobid]
            munger.update({'status':newstatus,'output':joboutput,'lastUpdate':timeNow()})
            db.update({jobid:munger})
            db.commit()
            return True
        else:
            return False

def parse_request(req):
    """
    Parses application/json request body data into a Python dictionary
    needs urllib.parse.unquote_plus±
    """
    payload = req.get_data()
    payload = unquote_plus(payload)
    payload = re.sub('payload=', '', payload)
    payload = json.loads(payload)

    return payload