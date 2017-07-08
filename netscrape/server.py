import os
import logging

from flask import Flask
from flask_cors import CORS
from pymongo import MongoClient
from flask_restful import reqparse, Api, Resource, abort, inputs

from netscrape.auth import *
from netscrape.daemon import daemon
from netscrape.db_interface import db_interface


logging.basicConfig(filename="netscrape.log", level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p")
app = Flask(__name__)
CORS(app) # Enable CORS
logging.info("Starting server.")
client = MongoClient(os.environ["MONGO_URI"])
system_db = "sys"
data_db = "data"
schedule_col = "schedule"

try:
    interface = db_interface(client, system_db, data_db, schedule_col, username=os.environ["MONGO_USER"], password=os.environ["MONGO_PASS"])
except KeyError:
    logging.info("Running without authentication.")
    interface = db_interface(client, system_db, data_db, schedule_col)
daemon(interface)

# Set up body parsing for put
parser = reqparse.RequestParser()
parser.add_argument("name", required=True)
parser.add_argument("description", required=False)
parser.add_argument("next", type=int, required=True)
parser.add_argument("every", type=int, required=True)
parser.add_argument("times", type=int, required=True)
parser.add_argument("save", type=inputs.boolean, required=True)
parser.add_argument("schema", type=inputs.boolean, required=True)
parser.add_argument("function", required=True)

# Set up body parsing for update
fuzzy_parser = reqparse.RequestParser()
fuzzy_parser.add_argument("name")
fuzzy_parser.add_argument("description")
fuzzy_parser.add_argument("next", type=int)
fuzzy_parser.add_argument("every", type=int)
fuzzy_parser.add_argument("times", type=int)
fuzzy_parser.add_argument("save", type=inputs.boolean)
fuzzy_parser.add_argument("schema", type=inputs.boolean)
fuzzy_parser.add_argument("function")

def service_failed(e):
    logging.exception("Unable to fulfill request. " + str(e))
    return abort(400, message="Unable to fulfill request: " + str(e))


class Schedule(Resource):
    
    @requires_auth
    def get(self):
        try:
            return interface.get_schedule(), 200
        except Exception as e:
            return service_failed(e)

    @requires_auth
    def put(self):
        try:
            args = parser.parse_args()
            nav = interface.put_navigator(args)
            if nav:
                return nav, 201
            else:
                return "A navigator with the name " + args["name"] + " already exists.", 409
        except Exception as e:
            return service_failed(e)


class Navigator(Resource):

    @requires_auth
    def get(self, navigator_name):
        try:
            nav = interface.get_navigator(navigator_name)
            if nav:
                return nav, 200
            else:
                return "A navigator with the name " + navigator_name + " does not exist.", 404
        except Exception as e:
            return service_failed(e)

    @requires_auth
    def patch(self, navigator_name):
        try:
            return interface.update_navigator(navigator_name, fuzzy_parser.parse_args())
        except Exception as e:
            return service_failed(e)

    @requires_auth
    def delete(self, navigator_name):
        try:
            return interface.delete_navigator(navigator_name)
        except Exception as e:
            return service_failed(e)


class OneData(Resource):

    @requires_auth
    def get(self, navigator_name):
        try:
            nav = interface.get_newest_data(navigator_name)
            if nav:
                return nav, 200
            else:
                return "A navigator with the name " + navigator_name + " does not exist.", 404
        except Exception as e:
            return service_failed(e)


class ManyData(Resource):

    @requires_auth
    def get(self, navigator_name):
        try:
            nav = interface.get_history(navigator_name)
            if nav:
                return nav, 200
            else:
                return "A navigator with the name " + navigator_name + " does not exist.", 404
        except Exception as e:
            return service_failed(e)


# Set up routing
api = Api(app)
api.add_resource(Navigator, '/schedule/<navigator_name>')
api.add_resource(Schedule, '/schedule')
api.add_resource(OneData, '/data/<navigator_name>/top')
api.add_resource(ManyData, '/data/<navigator_name>')



app.run(host='0.0.0.0', port=os.environ["FLASK_PORT"])
