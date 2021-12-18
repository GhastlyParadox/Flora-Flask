from flask_restful import Resource, reqparse
from application.db.core import restify_keyedtuple
from application import logger


class PrimaryImageInfo(Resource):
    """
    Performs and returns a search against the specimen records.
    """

    def __init__(self, db):
        self.db = db

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, required=True, help='{error_msg}')
        opts = parser.parse_args()

        logger.debug("Search options: {0}".format(opts))

        try:
            image_record = self.db.get_primary_image_info(opts["id"])
        except Exception as e:
            logger.exception(str(e))
            return {'message': str(e)}

        if image_record:
            return restify_keyedtuple([image_record])[0]
        else:
            return {"message": "No image found"}


class AllImageInfo(Resource):
    """
    Performs and returns a search against the specimen records.
    """

    def __init__(self, db):
        self.db = db

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, required=True, help='{error_msg}')
        opts = parser.parse_args()

        logger.debug("Search options: {0}".format(opts))

        try:
            image_record_list = self.db.get_all_image_info(opts["id"])
        except Exception as e:
            logger.exception(str(e))
            return {'message': str(e)}

        if image_record_list:
            return restify_keyedtuple(image_record_list)
        else:
            return {"message": "No image found"}
