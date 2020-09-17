from .interface import JobsApi, StatusApi
from .auth import SignupApi, LoginApi
from .test import Test

def initialize_routes(api):
    api.add_resource(Test,'/')
    api.add_resource(SignupApi, '/api/auth/signup')
    api.add_resource(LoginApi, '/api/auth/login')
    api.add_resource(JobsApi, '/api/jobmanager')
    api.add_resource(StatusApi, '/api/status/<id>')

    