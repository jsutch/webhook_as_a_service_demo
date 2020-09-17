"""
Custom Errors
"""
class InternalServerError(Exception):
    pass

class SchemaValidationError(Exception):
    pass

class JobAlreadyExistsError(Exception):
    pass

class UpdatingJobError(Exception):
    pass

class DeletingJobError(Exception):
    pass

class JobNotExistsError(Exception):
    pass

class EmailAlreadyExistsError(Exception):
    pass

class UnauthorizedError(Exception):
    pass

class ExpiredTokenError(Exception):
    pass

class EmailDoesnotExistsError(Exception):
    pass

class BadTokenError(Exception):
    pass

errors = {
    "InternalServerError": {
        "message": "Something went wrong",
        "status": 500
        },
    "SchemaValidationError": {
        "message": "Request is missing required fields",
        "status": 400
        },
    "JobAlreadyExistsError": {
        "message": "Job with given name already exists",
        "status": 400
        },
    "UpdatingJobError": {
        "message": "Updating movie added by other is forbidden",
        "status": 403
        },
    "DeletingJobError": {
        "message": "Deleting movie added by other is forbidden",
        "status": 403
        },
    "JobNotExistsError": {
        "message": "Job with given id doesn't exists",
        "status": 400
        },
    "EmailAlreadyExistsError": {
        "message": "User with given email address already exists",
        "status": 400
        },
    "UnauthorizedError": {
        "message": "Invalid username or password",
        "status": 401
        },
    "ExpiredTokenError": {
        "message": "Token expired",
        "status": 403
        },
    "BadTokenError": {
        "message": "Invalid token",
        "status": 403
        },
    "EmailDoesnotExistsError": {
        "message": "Couldn't find the user with given email address",
        "status": 400
        }
   }
