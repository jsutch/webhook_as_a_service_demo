#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
This is a worker for a simple Webhook As A Service worker to show basic code functionality for smallish jobs. 
A simple poller system looks in a job database for a job with a status of 'accepted', then
- changes the status to started 
- unpacks the api call inside
- runs the api call with the components from within supplied header, method and json data
- attempts to retry the call if a non-200 response is received
- captures output from the call to the job database
- attempts to call a provided "callback" listener and updates the database with the captured output

TODO general notes:
A production version of this would be better:
- using something like celery/redis/rabbitmq or kafka instead of a local datastore/poller
- multiprocess to improve scaling
- refactored so that the code runners, pollers, updaters and API callers were rebuilt as classes
- enable larger inputs and outputs by saving input/output data in some other way. the local nosql store won't scale
- adding the flask rate limiter
- et al

"""
import sys
sys.path.append('/usr/local/lib/python3.8/site-packages')

# set docker path:
appPath='/var/www/webhook/app'

# database
import sqlitedict
sqlitedict.PICKLE_PROTOCOL = 4 #try to overcome the HIGHEST PICKLE problem
from sqlitedict import SqliteDict
jobsdb = SqliteDict('/var/www/webhook/app/jobs.db', autocommit=True)

# multiprocessing 
import multiprocessing as mp

# basics
from datetime import datetime
import logging, time, random, requests, json

# tenacity retry handler
# https://github.com/jd/tenacity
import tenacity
from tenacity import retry, wait_exponential, stop_after_attempt, wait_fixed

#TEST =  open('XXXXXXX','a')
#TEST.write("XXXXX\n")
#TEST.close()

__author__ = "Jeff Sutch"
__copyright__ = "Copyright 2020, Collett Park Networks"
__credits__ = ["Jeff Sutch"]
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = "Jeff Sutch"
__email__ = "jeff@collettpark.com"
__status__ = "Demo"


# test url targets
# flakyurl = 'http://snout:7777/service'
# badurl = 'http://snout:7778/noservice'
# goodurl = 'http://snout:7777/mostlygood'
# junkurl = 'http://localhost:7777/noservice'


# start logging
logging.basicConfig(filename='/var/www/webhook/app/worker.log',level=logging.INFO)
logger = logging.getLogger()
# http logging for debugging
# import http.client as http_client
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True
# http_client.HTTPConnection.debuglevel = 1


# standard defs
def timeNow():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")

# db polling functions
# check for newly accepted jobs
def pollnew():
    """
    check for jobs with 'accepted' status
    """
    return [(k) for k, v in jobsdb.items() if v['status'] == 'accepted']

# check for jobs ready to run
def pollrun():
    """
    check for jobs with 'started' status
    """
    return [(k) for k, v in jobsdb.items() if v['status'] == 'started']

def pollcompleted():
    completed = ['completed','failed','ok', 'sent']
    return [(k) for k, v in jobsdb.items() if v['status'] in completed]

def pollnotified():
    """
    check for jobs with ['notified','failed_notify'] status
    """
    notified = ['notified','failed_notify','true']
    return [(k) for k, v in jobsdb.items() if v['status'] in notified]

def pollnotnotified():
    """
    check for jobs with with notified = 'no'
    """
    return [(k) for k, v in jobsdb.items() if v['notified'] == 'no']
    

# db update functions
def updateStatus(jobid, newstatus, joboutput="Not Passing Job Output"):
    """
    update the database status for 'jobid' with 'status'
    TODO:
    - limit to known status types
    """
    print("UpdateStatus PARMS: ", jobid, newstatus, joboutput)
    db = SqliteDict('/var/www/webhook/app/jobs.db', autocommit=True)
    if jobid:
        with db:
            munger = db[jobid]
            munger.update({'status':newstatus,'output':joboutput,'lastUpdate':timeNow()})
            db.update({jobid:munger})
            db.commit()
            return True
    else:
        return False


# Main API testing function
# can customize retries and backoffs here
# @retry(reraise=True,wait=wait_exponential(),stop=stop_after_attempt(10))
# @retry(reraise=True,wait=wait_fixed(1), stop=stop_after_attempt(3))
@retry(reraise=True,wait=wait_fixed(1), stop=stop_after_attempt(1)) # testing
def geturl(jobId):
    """
    Main executor logic. Retry logic is in the tenacity decorator.
    TODO:
    - handle hard 400 fails without retry
    - sanitize header and data input
    - except on linting/santizing errors
    """
    # i need the url, the method, the headers and the body
    # do the lookup
    if jobId in jobsdb:
        job = dict(jobsdb[jobId])
        clientMethod = job['methodtype']
        clientUrl = job['service']   
        clientHeaders = job['headers']
        clientData = job['data']

    try:
        print("GETURL parms: ", clientUrl, clientHeaders, clientData)
        if clientMethod == 'POST':
            usemethod = requests.post
        elif clientMethod =='GET':
            usemethod = requests.get

        r = usemethod(clientUrl, data=json.dumps(clientData), headers=clientHeaders)
        r.raise_for_status() # tenacity won't work without this here
        print("GETURL Return: ", r.status_code, r.text)
        return 'completed', (r.status_code, r.text)
    except requests.exceptions.HTTPError as err:
        print("GETURL HTTP Error", err)
        r.raise_for_status() #tenacity won't work without this here
        # print("GETURL Statistics:", geturl.retry.statistics)
        return 'http failed', str(err)
    except Exception as err2:
        print("GETURL General Error", err2)
        return 'failed with', str(err2)
    

def testurl(id):
    """
    more abstracted - presume the urlget logic does all the work
    """
    try:
        output = geturl(id)
        print("TestURL: ", output)
        if output:
            return 'completed', output
    except Exception as e:
        print("TestURL Exception: ", e)
        return 'failed', e



# Main workers logic
def job_starter():
    """
    Move jobs with 'accepted' state to 'started' state for the runner to pick up
    TODO:
    - 
    """
    newjobs = pollnew()[:10]
    if newjobs is None:
        return
    for n in pollnew():
        print('start job', n)
        try:
            logger.info('accepted job %s at %s', n, timeNow())
            #update_starter = updateStatus(n, 'started', 'waiting')
            updateStatus(n, 'started', 'waiting')
            logger.info('job %s finished with status %s at %s', n, 'started', timeNow())
        except Exception as e:
            logger.warn('job_starter exception: job  %s failed at %s with %s', n, timeNow(), e)
            return f"job_starter exception: job {n} not started", e


def job_runner():
    """
    get a list of jobs in 'started' state, run the executor on them and record the return status
    TODO:
    - limit batch of jobs
    - add threader/multiprocessing to run jobs concurrently
    """
    runnablejobs = pollrun()[:10]
    if runnablejobs is None:
        return
    for j in pollrun():
        print('start runner', j)
        try:
            logger.info('runner job %s started at %s', j, timeNow())
            # change status to running
            updateStatus(j, 'running', 'not finished')
            # main executor:
            print('Job Runner: Starting testurl')
            jobstatus = testurl(j) 
            print('Job Runner testurl Finished')
            # update db status
            print("Job Runner - Updating", j, jobstatus[0],jobstatus[1])
            updateStatus(j, jobstatus[0],jobstatus[1]) # everything has an output tuple now
            logger.info('runner job %s finished with status %s at %s', j, jobstatus, timeNow())
        except Exception as e:
            print('Job Runner Exception', j, e)
            logger.info('runner job %s failed at %s with %s', j, timeNow(), e)
            return 'runner job failed', e
    #print('Job Runner Finished - ok')


# Main Callback functions and logic
def updateNotify(jobid,notifystatus,notifyoutput="Not Passing Notify Output"):
    """
    update the database status for 'jobid' with 'status'
    TODO:
    - limit to known status types
    """
    db = SqliteDict('/var/www/webhook/app/jobs.db', autocommit=True)
    if jobid:
        with db:
            munger = db[jobid]
            munger.update({'notified':notifystatus,'notifyoutput':notifyoutput,'lastUpdate':timeNow()})
            db.update({jobid:munger})
            db.commit()
            return True
    else:
        return False

@retry(wait=wait_fixed(1), stop=stop_after_attempt(2))
def cburl(id):
    """
    Main callback logic. Retry logic is in the tenacity decorator.
    TODO:
    - get url/headers/data as fields from the jobsdb
    - sanitize callback url
    - sanitize header and data input
    - except on linting/santizing errors
    """
    cbdata = jobsdb[id]
    print("callback", id, datetime.now().strftime('%Y-%m-%d-%H:%M:%S'))
    cburl, cbheaders = cbdata['callback'], cbdata['headers']
    cbdata = {'clientId':cbdata['clientId'], 'status':cbdata['status'],'lastUpdate':cbdata['lastUpdate'], 'jobId':cbdata['jobId'],'job_output':str(cbdata['output'])}
    try:
        print("CBURL parms: ", cburl, cbheaders, cbdata)
        r = requests.post(url=cburl, headers=cbheaders, data=json.dumps(cbdata))
        r.raise_for_status()
        return 'callback sent', r.status_code
    except requests.exceptions.HTTPError as err:
        print("CBURL HTTP Exception", str(err))
        r.raise_for_status() #tenacity won't work without this here
        return '***http failed***', str(err)
    except Exception  as err2:
        # General exception - fail without retry
        # r.raise_for_status() #tenacity won't work without this here
        return '*** callback general failure***', str(err2)


def testcb(id):
    """
    error wrapper for callbacks
    """
    try:
        print('testcb', id)
        notify = cburl(id)
        if notify:
            return 'true', notify
    except Exception as e:
        return '***notification_failed***', str(e)

def cb_runner():
    """
    master loop for callback function. pass id to testcb -> cburl
    TODO:
    - add threader/multiprocessing to run jobs concurrently
    """
    finishedjobs = pollcompleted()[:10]
    if finishedjobs is None:
        return
    # need jobs that are completed but haven't been notified
    for c in finishedjobs:
        if jobsdb[c]['notified'] == 'no':
            try:
                logger.info('callback job %s started at %s', c, timeNow())
                cbdata = jobsdb[c]
                print('cb_runner', c)
                cbstatus = testcb(c)
                print("CB Runner status: ", c, type(cbstatus), cbstatus[0], cbstatus[1])
                # add a new notified field so the job status persists
                updateNotify(c, cbstatus[0], str(cbstatus[1]))
                logger.info('callback job %s finished with notification status %s at %s', c, cbstatus, timeNow())
            except Exception as e:
                print('callback exception', e)
                logger.info('callback job %s failed at %s with %s', c, timeNow(), e)
                return 'callback job failed', e


def main_loop():
    # print("beginning worker instance at ", timeNow())
    logger.debug('worker instance %s',  timeNow())
    job_starter()
    time.sleep(1)
    # job runner loop
    job_runner()
    time.sleep(1)
    # Callback loop
    cb_runner()
    time.sleep(1)
    # wait 
    time.sleep(1)



if __name__ == '__main__':
    print("beginning worker instance at ", timeNow())
    while True:
        # queue = mp.Queue()
        main_loop()
