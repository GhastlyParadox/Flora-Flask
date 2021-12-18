from flask_restful import Resource, reqparse
from application.db.miflora import MIFloraDB
from application.db.core import restify_keyedtuple
from application import logger


class SpecimenSearch(Resource):
    """
    Performs and returns a search against the specimen records.
    """

    def __init__(self, db):
        self.db = db

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("n_results", type=int, default=MIFloraDB.default_n_results)
        parser.add_argument("offset", type=int, default=MIFloraDB.default_offset)
        parser.add_argument("common_name", type=str, default="")
        parser.add_argument("scientific_name", type=str, default="")
        parser.add_argument("genus", type=str, default="")
        parser.add_argument("family", type=str, default="")
        parser.add_argument("collector", type=str, default="")
        parser.add_argument("collector_number", type=str, default="")
        parser.add_argument("collection_year", type=str, default="")
        parser.add_argument("location", type=str, default="")
        parser.add_argument("county", type=str, default="")
        parser.add_argument("identity", type=int, default=0)
        search_options = parser.parse_args()

        logger.debug("Search options: {0}".format(search_options))

        try:
            specimen_records = self.db.search_specimens(n_results=search_options["n_results"],
                                                        offset=search_options["offset"],
                                                        common_name=search_options["common_name"],
                                                        scientific_name=search_options["scientific_name"],
                                                        genus=search_options["genus"],
                                                        family=search_options["family"],
                                                        collector_name=search_options["collector"],
                                                        collector_number=search_options["collector_number"],
                                                        collection_year=search_options["collection_year"],
                                                        location=search_options["location"],
                                                        county=search_options["county"],
                                                        identity=search_options["identity"])

            logger.debug("Record Count: {0}".format(len(specimen_records)))
        except Exception as e:
            logger.exception(str(e))
            return {'message': str(e)}

        if specimen_records:
            return restify_keyedtuple(specimen_records)
        else:
            return {"message": "No records found"}


class SpecimenSearchSpecify(Resource):
    """
    Performs and returns a search against the specimen records.
    """

    def __init__(self, db):
        self.db = db

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("n_results", type=int, default=MIFloraDB.default_n_results)
        parser.add_argument("offset", type=int, default=MIFloraDB.default_offset)
        parser.add_argument("common_name", type=str, default="")
        parser.add_argument("scientific_name", type=str, default="")
        parser.add_argument("genus", type=str, default="")
        parser.add_argument("family", type=str, default="")
        parser.add_argument("collector", type=str, default="")
        parser.add_argument("collector_number", type=str, default="")
        parser.add_argument("collection_year", type=str, default="")
        parser.add_argument("location", type=str, default="")
        parser.add_argument("county", type=str, default="")
        parser.add_argument("plant_id", type=int, default=0)
        parser.add_argument("catalog_number", type=str, default="")
        search_options = parser.parse_args()

        logger.debug("Search options: {0}".format(search_options))

        try:
            specimen_records = self.db.search_specimens_sp(n_results=search_options["n_results"],
                                                           offset=search_options["offset"],
                                                           common_name=search_options["common_name"],
                                                           scientific_name=search_options["scientific_name"],
                                                           genus=search_options["genus"],
                                                           family=search_options["family"],
                                                           collector_name=search_options["collector"],
                                                           collector_number=search_options["collector_number"],
                                                           collection_year=search_options["collection_year"],
                                                           location=search_options["location"],
                                                           county=search_options["county"],
                                                           plant_id=search_options["plant_id"],
                                                           catalog_number=search_options["catalog_number"])

            logger.debug("Record Count: {0}".format(len(specimen_records)))
        except Exception as e:
            logger.exception(str(e))
            return {'message': str(e)}

        if specimen_records:
            return restify_keyedtuple(specimen_records)
        else:
            return {"message": "No records found"}
