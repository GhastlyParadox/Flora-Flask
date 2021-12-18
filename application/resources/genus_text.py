from flask_restful import Resource, reqparse
from application import logger


class GenusText(Resource):
    """
    Returns the descriptive html text associated with a species id.
    """

    def __init__(self, db):
        self.db = db

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=str, required=True, help='{error_msg}')
        opts = parser.parse_args()

        logger.debug("REST options: {0}".format(opts))

        try:
            genus_text = self.db.get_flora_genus_text(opts["id"])
        except Exception as e:
            logger.exception(str(e))
            return {'message': str(e)}

        if genus_text is None:
            return {"message": "No text found"}
        else:
            return {"text": "{0}".format(genus_text)}
