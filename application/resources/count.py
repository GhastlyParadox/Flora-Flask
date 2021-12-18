from flask_restful import Resource
from application.db.miflora import SpecimenRecords
from application import logger


class TotalRecordCount(Resource):
    """
    Returns the number of specimen records available.  This is not a super useful resource, but is an easy test call
    to make sure the basic REST setup is functioning.
    """

    def __init__(self, db):
        self.db = db

        logger.debug("Creating TotalRecordCount")

    def get(self):
        logger.debug('Getting TotalRecordCount')

        db_count = 0

        try:
            db_count = self.db.get_count(SpecimenRecords.identity)
            logger.debug("Total record count: {0}".format(db_count))
        except Exception:
            logger.exception("TotalRecordCount")

        return {'n_records': "{0}".format(db_count)}
