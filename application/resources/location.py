from flask_restful import Resource, reqparse
import logging

logger = logging.getLogger(__name__)


class ListLocations(Resource):
    """
    Returns the list of locations associated with a plant ID.
    """

    def __init__(self, db):
        self.db = db

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, required=True, help='{error_msg}')
        opts = parser.parse_args()

        logger.debug("REST options: {0}".format(opts))

        try:
            locations = self.db.list_locations(opts["id"])
        except Exception as e:
            logger.exception(str(e))
            return {'message': str(e)}

        if locations:
            return {"locations": locations}
        else:
            return {"message": "No locations found"}


class ListLocationsSpecify(Resource):
    """
    Returns the list of locations associated with a plant ID.
    """

    def __init__(self, db):
        self.db = db

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, required=True, help='{error_msg}')
        opts = parser.parse_args()

        logger.debug("REST options: {0}".format(opts))

        try:
            locations = self.db.list_locations_sp(opts["id"])
        except Exception as e:
            logger.exception(str(e))
            return {'message': str(e)}

        if locations:
            return {"locations": locations}
        else:
            return {"message": "No locations found"}
