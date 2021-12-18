from flask import current_app as app
from application import flora_db
from flask_restful import Api
from .count import TotalRecordCount
from .specimen_search import SpecimenSearch, SpecimenSearchSpecify
from .flora_search import FloraSearch, FloraSearchSpecify
from .species_text import SpeciesText
from .family_text import FamilyText
from .genus_text import GenusText
from .homepages_text import HomePagesText
from .image import PrimaryImageInfo, AllImageInfo
from .location import ListLocations, ListLocationsSpecify

API_URL = "/api/v1.0/"
api = Api(app)

# Add any of the REST resources here...
# The _sp versions *should* do the same thing as their predecessors, but using the specify export table instead of the
# various county location tables and specimen records table.
api.add_resource(TotalRecordCount, API_URL + "count", resource_class_args={flora_db})
api.add_resource(SpecimenSearch, API_URL + "spec_search", resource_class_args={flora_db})
api.add_resource(SpecimenSearchSpecify, API_URL + "spec_search_sp", resource_class_args={flora_db})
api.add_resource(FloraSearch, API_URL + "flora_search", resource_class_args={flora_db})
api.add_resource(FloraSearchSpecify, API_URL + "flora_search_sp", resource_class_args={flora_db})
api.add_resource(SpeciesText, API_URL + "spec_text", resource_class_args={flora_db})
api.add_resource(GenusText, API_URL + "genus_text", resource_class_args={flora_db})
api.add_resource(FamilyText, API_URL + "family_text", resource_class_args={flora_db})
api.add_resource(HomePagesText, API_URL + "homepages_text", resource_class_args={flora_db})
api.add_resource(PrimaryImageInfo, API_URL + "pimage_info", resource_class_args={flora_db})
api.add_resource(AllImageInfo, API_URL + "allimage_info", resource_class_args={flora_db})
api.add_resource(ListLocations, API_URL + "locs", resource_class_args={flora_db})
api.add_resource(ListLocationsSpecify, API_URL + "locs_sp", resource_class_args={flora_db})
