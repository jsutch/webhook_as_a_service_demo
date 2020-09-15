# Webhook As A Service demo

This is a basic 3 tier Web/App/DB service that allows an authenticated client to pass crafted http payloads (url/header/body) to a service. The service stores the query, then runs it from a batch, recording the reply. Then a Callback batch contacts the callback URL supplied with an outcome of the job run. 

### This is demo code to show functionality and get feedback - not ready for production
 This is meant to demonstrate a basic service working in a single docker container, quickly patterned, so the standard stuff (gunicorn, kafka, JWTs/Bearer tokens, Flask reqparse, breaking Apis into classes and files, Unit Tests, etc) didn't make it mostly for reasons of Time or "More Than One Container".  There are copious notes about all the stuff I would refactor before moving it to production.

#### Docker notes
The package will build into a single docker container that runs a flask app listener and a worker - both will reference a local nosql datastore. Supervisord runs the services and the startup logic is controlled from supervisord.conf. There are some files for gunicorn and uwsgi, but those aren't integrated and tested with this package yet. 

You can build and start with this bash command line:
```bash
alias dk='docker';
dk build -t "webhook:latest"  app/ && export DKID=$(dk run -d -p 6666:6666  webhook) && dkps && sleep 5; dk exec $DKID ps -eaf
```

#### Retry/Backoff logic
 Retries are enabled through the tenacity tool in worker.py for both the geturl() and cburl() methods. These examples are basic, but much more complex and robust logic is possible.  
[Tenacity Github Page](https://github.com/jd/tenacity)

**exponential backoff**  
```
@retry(reraise=True,wait=wait_exponential(),stop=stop_after_attempt(10))
```

**static retry after 2 seconds for 5 attempts**   
```
@retry(reraise=True,wait=wait_fixed(2), stop=stop_after_attempt(5))
```

**testing - static 1 second wait and 1 attempt**    
```
@retry(reraise=True,wait=wait_fixed(1), stop=stop_after_attempt(1))
```

#### Datastores
 The Datastores are sqlitedict and the tokens.db is populated with demo credentials at start - these can be found in tokens_intitialize.py. jobs.db and sessions.db are blank at start and reloading.

#### Secret Key
 There is a Flask secret key included in this code that you'll want to change before running on an outward facing system. 

#### TLS/Certificates:  
  If you have full certs, the logic is there to run this with TLS connections - just put your certs under app/certs and uncomment the correct lines in main.py and supervisord.conf, ensuring that paths and names are correct. 






API methods:

### /webhook
### accepts GET and POST methods

- POST authenticates, then accepts a job package to add to the job queue

Headers, service, methodtype and data should be formatted such that the raw data can be passed to the requests library to handle in a "url=, headers= and data=" format. This service does no rewriting or validating the data - it just runs the API call, records the outcome and delivers the information to the callback 

Accepts:  
```json
{
    "client_id": "myclientId",
    "verify_token":"myclienttoken"
    "service": "http://my_url/my_service",
    "methodtype":"POST",
    "headers":  {"serviceAuthId":"my_service_user","serviceAuthToken":"my_service_password","user-agent": "named_user_agent","Content-Type":"typically application/json or application/x-www-form-urlencoded"},
    "callback": "http://clients_callback_url/callback",
    "data": JSON formatted Data: e.g. {"userId": 1,"id": 5,"title": "laboriosam mollitia et enim quasi adipisci quia provident illum","completed": false}
 
}
```

Returns:  
```json
{
    "created": "RFC 8601 formatted date/time (reverse datestamp with microseconds)",
    "job_id": "job id in UUID4 format (e.g 4524330d-9abc-496f-b4ee-423733c3d0ed)",
    "status": "job status - only 'accepted' currently implemented"
}
```

Will fail with:
```json
{
    "message": "request type must be JSON",
    "status": "failed"
}
```

or 
```json
{
    "status": "bad credentials"
}
```

Callbacks - this service also attempts callback retry logic and traps outcomes and errors related to the callback attempt. Those are also stored in the database and can be accessed with the /status method

- GET validates auth tokens and refreshes the session database

Accepts:  
```json
{
    "client_id": "myClientId",
    "verify_token":"myVerifyToken"
}
```

Returns:  
```json
{
    "status": "success"
}
```

or
```json
{
    "status": "bad credentials"
}
```


### /status
### Accepts GETs

Status is an authenticated service that lets a client retrieve the last known status of a particular job. Returns JSON

job statuses can be:
- accepted - added to queue
- started - ready to run
- running - in a run or retry state
- completed - successfully run or failed after multiple retries
- failed - something went wrong executing the API run

- output - the output or errors from the API run
- notified - "sent, notification failed"
- notifyoutput - output or errors from callback




Accepts:  
```json
{
    "client_id": "66666666666668",
    "verify_token":"d7811aa4852d7c021df3da133f8d3e11ad1e5c42d3ed0a1a",
    "job_id": "6b7d7b4b-6d76-4fed-8306-330cb945cca0"
}
```

Returns:  
```json
{
    "jobId": "6b7d7b4b-6d76-4fed-8306-330cb945cca0",
    "lastUpdate": "2020-09-14 00:12:03:357853",
    "notified": "notification failed",
    "output": "None",
    "service": "http://mycallback.mycompany.com/callback",
    "status": "completed"
}
```

A nonexistent or malformed job id will return:
```json
{
    "status": "No job with that ID exists"
}
```

Examples:

A Successful job would look something like this:  
```json
{
    "client_id": "66666666666668",
    "verify_token":"d7811aa4852d7c021df3da133f8d3e11ad1e5c42d3ed0a1a",
    "job_id": "70205fb9-d8e8-43cd-ac2c-d25e6d69be20"
}

{
    "jobId": "70205fb9-d8e8-43cd-ac2c-d25e6d69be20",
    "lastUpdate": "2020-09-14 15:39:48:291420",
    "notified": "true",
    "notifyoutput": "('callback sent', 200)",
    "output": "('completed', (200, '{\\n  \"args\": {}, \\n  \"data\": \"{\\\\\"userId\\\\\": 1, \\\\\"id\\\\\": 5, \\\\\"title\\\\\": \\\\\"laboriosam mollitia et enim quasi adipisci quia provident illum\\\\\", \\\\\"completed\\\\\": false}\", \\n  \"files\": {}, \\n  \"form\": {}, \\n  \"headers\": {\\n    \"Accept\": \"*/*\", \\n    \"Accept-Encoding\": \"gzip, deflate\", \\n    \"Content-Length\": \"118\", \\n    \"Content-Type\": \"application/json\", \\n    \"Host\": \"httpbin.org\", \\n    \"Serviceauthid\": \"successfulcorp\", \\n    \"Serviceauthtoken\": \"rjc9uBixhWZ2l52mEMViGJfyQh5QfL6wAeuuCl0AsB4=\", \\n    \"User-Agent\": \"my-app/0.0.1\", \\n    \"X-Amzn-Trace-Id\": \"Root=1-5f5ff133-5c93454b223272bfba737911\"\\n  }, \\n  \"json\": {\\n    \"completed\": false, \\n    \"id\": 5, \\n    \"title\": \"laboriosam mollitia et enim quasi adipisci quia provident illum\", \\n    \"userId\": 1\\n  }, \\n  \"origin\": \"174.21.151.247\", \\n  \"url\": \"https://httpbin.org/post\"\\n}\\n'))",
    "service": "https://httpbin.org/post",
    "status": "completed"
}
```



A retried job that failed retries with a failed callback would look something like this:

```json
{
    "client_id": "66666666666668",
    "service": "armor",
    "verify_token":"d7811aa4852d7c021df3da133f8d3e11ad1e5c42d3ed0a1a",
    "job_id": "11c6a673-5eec-404e-a1c0-fbddca2ad81b"
}

{
    "jobId": "f8170b53-6306-4035-ba2a-8657a3cc4297",
    "lastUpdate": "2020-09-14 15:34:24:550903",
    "notified": "true",
    "notifyoutput": "('*** callback general failure***', \"HTTPConnectionPool(host='snout', port=7777): Max retries exceeded with url: /callback (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x103f50510>: Failed to establish a new connection: [Errno 61] Connection refused'))\")",
    "output": "('failed with', \"HTTPConnectionPool(host='snout', port=7777): Max retries exceeded with url: /service (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x103f4c290>: Failed to establish a new connection: [Errno 61] Connection refused'))\")",
    "service": "http://snout:7777/service",
    "status": "completed"
}
```




## Contact/Troubleshoot
jeff@collettpark.com

