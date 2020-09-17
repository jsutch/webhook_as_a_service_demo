from flask_restful import Resource

class Test(Resource):
    """
    test harness. 
    """
    def get(self):
        """
        testing 
        """
        return "This is a web return", 200