# from .interface import InterfaceApi, StatusApi
from .test import Test

def initialize_routes(api):
    api.add_resource(Test,'/')
    # api.add_resource(InterfaceApi, '/api/jobmanager')
    # api.add_resource(StatusApi, '/api/status/<id>')