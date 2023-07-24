from flask import current_app
from flask_restful import Resource


class WorkLoad(Resource):
    def get(self):
        return f"Pending requests: {current_app.config['PENDING_REQUESTS']}"
