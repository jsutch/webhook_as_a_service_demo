#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from .db import db
from database.models import Jobs

# general imports
import logging, time, random, requests, json, os

from datetime import datetime
# from tenacity import retry, wait_exponential, stop_after_attempt, wait_fixed
# new backoff stuff
from resources.errors import HTTPError
import backoff
class ServerError(requests.exceptions.HTTPError):
    pass

REQUESTS_MAX_RETRIES=3
# Re-usable decorator with exponential wait.
retry_timeout = backoff.on_exception(
    wait_gen=backoff.expo,
    exception=(
        ServerError,
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError
    ),
    max_tries=REQUESTS_MAX_RETRIES,
)

# geturl
@retry_timeout
def geturl(u,h,d):
    try:
        r = requests.post(url=u, headers=h, data=json.dumps(d))
        if r.status_code in [ 502,503,504,429]:
            raise ServerError("failed", r.status_code, r.text)
        return r.json(),r.status_code
    except Exception as e:
        raise ServerError("failed", r.status_code, r.text)
        return r.json(),r.status_code, e

def testurl(u,h,d):
    """
    more abstracted - presume the urlget logic does all the work
    """
    try:
        output = geturl(u,h,d)
        print("TestURL: ", output)
        if output:
            return 'completed', output
    except Exception as e:
        print("TestURL Exception: ", e)
        return 'failed', e


# poll for accepted jobs
# run the jobs
# run the callbacks


