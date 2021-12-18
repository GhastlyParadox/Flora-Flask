from flask_restful import Resource, reqparse
from application.db.miflora import MIFloraDB
from application.db.core import restify_keyedtuple
from application import logger


class FloraSearch(Resource):
    """
    Performs and returns a search against the MI Flora records.
    """

    def __init__(self, db):
        self.db = db

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("n_results", type=int, default=MIFloraDB.default_n_results)
        parser.add_argument("offset", type=int, default=MIFloraDB.default_offset)
        parser.add_argument("common_name", type=str, default="")
        parser.add_argument("scientific_name", type=str, default="")
        parser.add_argument("county", type=str, default="")
        parser.add_argument("wet", type=str, default="")
        parser.add_argument("w", type=int, default=None)
        parser.add_argument("na", type=str, default="")
        parser.add_argument("phys", type=str, default="")
        parser.add_argument("status", type=str, default="")
        parser.add_argument("family", type=str, default="")
        parser.add_argument("genus", type=str, default="")
        parser.add_argument("c", type=str, default="")
        parser.add_argument("plant_id", type=int, default="")
        search_options = parser.parse_args()

        logger.debug("Search options: {0}".format(search_options))

        try:
            flora_records = self.db.search_flora(n_results=search_options["n_results"],
                                                 offset=search_options["offset"],
                                                 common_name=search_options["common_name"],
                                                 scientific_name=search_options["scientific_name"],
                                                 county=search_options["county"],
                                                 wetness=search_options["wet"],
                                                 w=search_options["w"],
                                                 na=search_options["na"],
                                                 physiognomy=search_options["phys"],
                                                 status=search_options["status"],
                                                 family=search_options["family"],
                                                 genus=search_options["genus"],
                                                 coefficient=search_options["c"],
                                                 plant_id=search_options["plant_id"])

            logger.debug("Record Count: {0}".format(len(flora_records)))
        except Exception as e:
            logger.exception(str(e))
            return {'message': str(e)}

        if flora_records:
            return restify_keyedtuple(flora_records)
        else:
            return {"message": "No flora found"}


class FloraSearchSpecify(Resource):
    """
    Performs and returns a search against the MI Flora records.
    """

    def __init__(self, db):
        self.db = db

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("n_results", type=int, default=MIFloraDB.default_n_results)
        parser.add_argument("offset", type=int, default=MIFloraDB.default_offset)
        parser.add_argument("common_name", type=str, default="")
        parser.add_argument("scientific_name", type=str, default="")
        parser.add_argument("county", type=str, default="")
        parser.add_argument("wet", type=str, default="")
        parser.add_argument("w", type=int, default=None)
        parser.add_argument("na", type=str, default="")
        parser.add_argument("phys", type=str, default="")
        parser.add_argument("status", type=str, default="")
        parser.add_argument("family", type=str, default="")
        parser.add_argument("genus", type=str, default="")
        parser.add_argument("c", type=str, default="")
        parser.add_argument("plant_id", type=int, default="")
        search_options = parser.parse_args()

        logger.debug("Search options: {0}".format(search_options))

        try:
            flora_records = self.db.search_flora_sp(n_results=search_options["n_results"],
                                                    offset=search_options["offset"],
                                                    common_name=search_options["common_name"],
                                                    scientific_name=search_options["scientific_name"],
                                                    county=search_options["county"],
                                                    wetness=search_options["wet"],
                                                    w=search_options["w"],
                                                    na=search_options["na"],
                                                    physiognomy=search_options["phys"],
                                                    status=search_options["status"],
                                                    family=search_options["family"],
                                                    genus=search_options["genus"],
                                                    coefficient=search_options["c"],
                                                    plant_id=search_options["plant_id"])

            logger.debug("Record Count: {0}".format(len(flora_records)))
        except Exception as e:
            logger.exception(str(e))
            return {'message': str(e)}

        if flora_records:
            return restify_keyedtuple(flora_records)
        else:
            return {"message": "No flora found"}
