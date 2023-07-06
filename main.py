import os

from flask import Flask
from flask_restful import Api

from resources.line import Callback


app = Flask(__name__)
api = Api(app)

api.add_resource(Callback, "/callback")


if __name__ == "__main__":
    host = os.getenv("HOST")
    port = int(os.getenv("PORT"))
    app.run(host=host, port=port, debug=True)
