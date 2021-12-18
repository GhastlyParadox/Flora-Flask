from application import MIFLORA_BASE, logger
import json
from flask_sqlalchemy import BaseQuery, SQLAlchemy
from sqlalchemy import Column, String, Integer, DateTime, Float, Binary, or_, case, Text
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import column_property
from sqlalchemy import func
from .core import SpecimenSearchRecord, SpecifySearchRecord, ImageRecord, FloraSearchRecord


def join_miflora_to_common_names(search_query):
    # Join common names to michigan flora table
    search_query = search_query.outerjoin(CommonNames, MIFlora2010.plant_id == CommonNames.plant_id)
    return search_query


def join_miflora_to_synonyms(search_query):
    search_query = search_query.outerjoin(Synonyms, MIFlora2010.plant_id == Synonyms.plant_id)
    return search_query


def simple_join_specify_to_miflora(search_query):
    # Construct a query that joins specify specimens whose genus + species matches a given
    # the scientific_name field from Michigan Flora.
    # For specimens that are hybrids (species name contains ' × '--note this is unicode 00d7, NOT an x), join
    # them to both of the component species.
    search_query = search_query.join(SpecifyExport,
                                     SpecifyExport.plant_id == MIFlora2010.plant_id)
    return search_query


def join_specify_to_miflora(search_query):
    # Construct a query that joins specify specimens whose genus + species matches a given
    # the scientific_name field from Michigan Flora.
    # For specimens that are hybrids (species name contains ' × '--note this is unicode 00d7, NOT an x), join
    # them to both of the component species.
    search_query = search_query.join(SpecifyExport,
                                     or_(SpecifyExport.plant_id == MIFlora2010.plant_id,
                                         func.lower(MIFlora2010.scientific_name) == func.lower(
                                             func.concat(SpecifyExport.genus1, ' ',
                                                         func.left(SpecifyExport.species1,
                                                                   func.instr(SpecifyExport.species1, ' × ')))),
                                         func.lower(MIFlora2010.scientific_name) == func.lower(
                                             func.concat(SpecifyExport.genus1, ' ',
                                                         func.right(SpecifyExport.species1,
                                                                    func.length(SpecifyExport.species1) -
                                                                    func.instr(SpecifyExport.species1,
                                                                               ' × ') - 3)))))
    return search_query


def join_miflora_to_specify(search_query):
    # Construct a query that joins specify specimens whose genus + species matches a given
    # the scientific_name field from Michigan Flora.
    # For specimens that are hybrids (species name contains ' × '--note this is unicode 00d7, NOT an x), join
    # them to both of the component species.
    search_query = search_query.outerjoin(MIFlora2010,
                                          or_(func.lower(SpecifyExport.sci_name) == func.lower(
                                              MIFlora2010.scientific_name),
                                              func.lower(MIFlora2010.scientific_name) == func.lower(
                                                  func.concat(SpecifyExport.genus1, ' ',
                                                              func.left(SpecifyExport.species1,
                                                                        func.instr(SpecifyExport.species1, ' × ')))),
                                              func.lower(MIFlora2010.scientific_name) == func.lower(
                                                  func.concat(SpecifyExport.genus1, ' ',
                                                              func.right(SpecifyExport.species1,
                                                                         func.length(SpecifyExport.species1) -
                                                                         func.instr(SpecifyExport.species1,
                                                                                    ' × ') - 3)))))
    return search_query


class MIFloraDB(SQLAlchemy):

    default_n_results = 10
    default_offset = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def make_flora_search(self, n_results: int = default_n_results, offset: int = default_offset, common_name: str = "",
                          scientific_name: str = "", county: str = "", wetness: object = "", w: int = None,
                          na: str = "", physiognomy: str = "", status: object = "", family: str = "",
                          genus: str = "", coefficient: str = "", plant_id: int = None) -> BaseQuery:
        """
        Creates the Query object needed to perform a MI Flora record search.  To perform the actual search, one can
        either call the all() function on the object or use the search_flora() MIFloraDB class method which is really
        just calls this function with all().

        :return:
        :param n_results:
        :param offset:
        :param common_name:
        :param scientific_name:
        :param county:
        :param wetness:
        :param w:
        :param na:
        :param physiognomy:
        :param status:
        :param family:
        :param genus:
        :param coefficient:
        :param plant_id:
        :return:
        """

        search_query = self.session.query(FloraNames.plant_id, FloraNames.scientific_name, FloraNames.c,
                                          FloraNames.st, FloraNames.w, FloraNames.wet, FloraNames.phys,
                                          FloraNames.na, FloraNames.family_name)

        if common_name:
            search_query = search_query.filter(FloraNames.common_name.ilike('%{0}%'.format(common_name)))

        if scientific_name:
            search_query = search_query.filter(FloraNames.scientific_name.ilike('%{0}%'.format(scientific_name)))

        if wetness:
            if type(wetness) is not list:
                wetness = [wetness]

            search_query = search_query.filter(FloraNames.wet.in_(wetness))

        if w:
            search_query = search_query.filter(FloraNames.w == w)

        if na:
            search_query = search_query.filter(FloraNames.na == na)

        if physiognomy:
            if type(physiognomy) is not list:
                physiognomy = [physiognomy]

            search_query = search_query.filter(FloraNames.phys.in_(physiognomy))

        if status:
            if type(status) is not list:
                status = [status]

            search_query = search_query.filter(FloraNames.st.in_(status))

        if family:
            search_query = search_query.filter(FloraNames.family_name.ilike('%{0}%'.format(family)))

        if genus:
            search_query = search_query.filter(FloraNames.scientific_name.ilike('{0}%'.format(genus)))

        if coefficient:
            search_query = search_query.filter(FloraNames.c == coefficient)

        if county:
            if type(county) is not list:
                county = [county]

            sub_query = self.session.query(CoSpecies.plant_id)
            sub_query = sub_query.join(CountySpeciesLookup, CoSpecies.county == CountySpeciesLookup.place_name_db)
            sub_query = sub_query.filter(CountySpeciesLookup.place_name.in_(county))

            search_query = search_query.filter(FloraNames.plant_id.in_(sub_query))

        if plant_id:
            search_query = search_query.filter(FloraNames.plant_id == plant_id)

        search_query = search_query.distinct().order_by(FloraNames.scientific_name)

        # Limit our search so we don't return everything at once.  This effectively allows us to paginate the results.
        if n_results > 0:
            search_query = search_query.limit(n_results)

        if offset > 0:
            search_query = search_query.offset(offset)

        return search_query

    def specify_records_by_plant_id(self, plant_id):
        # Construct a query that returns the specify catalog numbers of specimens whose genus + species matches a given
        # plant_id from Michigan Flora.
        # For specimens that are hybrids (species name contains ' × '--note this is unicode 00d7, NOT an x), include
        # them in the search results for either of the component species.
        '''select distinct plant_id, `SCIENTIFIC NAME`, CatalogNumber, Genus1, Species1, instr(Species1, ' × '),
            concat(Genus1, ' ', left(Species1,instr(Species1, ' × '))), concat(Genus1, ' ', right(Species1,length(Species1) - instr(Species1, ' × ') -3))
          from tbl_michflora_export
          join MIFlora2010
          on lower(MIFlora2010.`SCIENTIFIC NAME`) = lower(concat(Genus1, ' ', left(Species1,instr(Species1, ' × '))))
            or lower(MIFlora2010.`SCIENTIFIC NAME`) = lower( concat(Genus1, ' ', right(Species1,length(Species1) - instr(Species1, ' × ') -3)))
          where instr(Species1, ' × ') > 0
          '''
        search_query = self.session.query(MIFlora2010.plant_id, SpecifyExport.species1, SpecifyExport.catalog_number)
        search_query = join_miflora_to_specify(search_query)
        search_query = search_query.filter(MIFlora2010.plant_id == plant_id)
        return search_query

    def make_flora_names_query(self, plant_id) -> BaseQuery:
        search_query = self.session.query(MIFlora2010.plant_id, MIFlora2010.scientific_name,
                                          MIFlora2010.c, MIFlora2010.st,
                                          MIFlora2010.w, MIFlora2010.wet, MIFlora2010.n_a, MIFlora2010.phys,
                                          MIFlora2010.family_name)
        search_query = search_query.outerjoin(PlantSpecies,
                                              PlantSpecies.plant_id == MIFlora2010.plant_id)
        search_query = search_query.outerjoin(Synonyms,
                                              Synonyms.plant_id == MIFlora2010.plant_id)
        search_query = search_query.outerjoin(CommonNames,
                                              CommonNames.plant_id == MIFlora2010.plant_id)
        search_query = search_query.filter(MIFlora2010.plant_id == plant_id)

        return search_query

    def make_flora_search_sp(self, n_results: int = default_n_results, offset: int = default_offset,
                             common_name: str = "",
                             scientific_name: str = "", county: str = "", wetness: object = "", w: int = None,
                             na: str = "", physiognomy: str = "", status: object = "", family: str = "",
                             genus: str = "", coefficient: str = "", plant_id: int = None) -> BaseQuery:

        search_query = self.session.query(MIFlora2010.plant_id, MIFlora2010.scientific_name, MIFlora2010.c,
                                          MIFlora2010.st, MIFlora2010.w, MIFlora2010.wet, MIFlora2010.phys,
                                          MIFlora2010.n_a, MIFlora2010.family_name, MIFlora2010.common_name,
                                          MIFlora2010.author)
        if common_name:
            search_query = join_miflora_to_common_names(search_query)
            search_query = search_query.filter(CommonNames.common_name.ilike('%{0}%'.format(common_name)))

        if scientific_name:
            search_query = search_query.filter(MIFlora2010.scientific_name.ilike('%{0}%'.format(scientific_name)))

        if wetness:
            if type(wetness) is not list:
                wetness = [wetness]

            search_query = search_query.filter(MIFlora2010.wet.in_(wetness))

        if w:
            search_query = search_query.filter(MIFlora2010.w == w)

        if na:
            search_query = search_query.filter(MIFlora2010.n_a == na)

        if physiognomy:
            if type(physiognomy) is not list:
                physiognomy = [physiognomy]

            search_query = search_query.filter(MIFlora2010.phys.in_(physiognomy))

        if status:
            if type(status) is not list:
                status = [status]

            search_query = search_query.filter(MIFlora2010.st.in_(status))

        if family:
            search_query = search_query.filter(MIFlora2010.family_name.ilike('{0}'.format(family)))

        if genus:
            search_query = search_query.filter(MIFlora2010.scientific_name.ilike('{0}%'.format(genus)))

        if coefficient:
            search_query = search_query.filter(MIFlora2010.c == coefficient)

        if county:
            if type(county) is not list:
                county = [county]

            sub_query = self.session.query(MIFlora2010.plant_id)
            sub_query = simple_join_specify_to_miflora(sub_query)
            # sub_query = sub_query.join(CountySpeciesLookup, CoSpecies.county == CountySpeciesLookup.place_name_db)
            # TODO: Deal with 'or' in the county field in specify... Also this is WAY too slow.
            sub_query = sub_query.filter(SpecifyExport.county.in_(county))
            search_query = search_query.filter(MIFlora2010.plant_id.in_(sub_query))

        if plant_id:
            search_query = search_query.filter(MIFlora2010.plant_id == plant_id)

        search_query = search_query.distinct().order_by(MIFlora2010.scientific_name)

        # Limit our search so we don't return everything at once.  This effectively allows us to paginate the results.
        if n_results > 0:
            search_query = search_query.limit(n_results)

        if offset > 0:
            search_query = search_query.offset(offset)

        return search_query

    def search_flora_sp(self, n_results=default_n_results, offset=default_offset, common_name="", scientific_name="",
                        county="", wetness="", w=None, na="", physiognomy="", status="", family="", genus="",
                        coefficient="", plant_id=None):
        search_query = self.make_flora_search_sp(n_results=n_results,
                                                 offset=offset,
                                                 common_name=common_name,
                                                 scientific_name=scientific_name,
                                                 county=county,
                                                 wetness=wetness,
                                                 w=w,
                                                 na=na,
                                                 physiognomy=physiognomy,
                                                 status=status,
                                                 family=family,
                                                 genus=genus,
                                                 coefficient=coefficient,
                                                 plant_id=plant_id)

        db_results = search_query.all()

        if db_results:
            return db_results
            records = list()
            for r in db_results:
                i_plant_id = 0
                r_list = list(r)
                r_list.append(self.list_common_names(r[i_plant_id]))
                records.append(FloraSearchRecord._make(r_list))

            return records
        else:
            return None

    def make_specimen_search_sp(self, n_results=default_n_results, offset=default_offset, common_name="",
                                scientific_name="", genus="", family="", collector_name="", collector_number="",
                                collection_year="", location="", county="", plant_id="", catalog_number=""):

        hidden_conditions = SpecifyExport.sensitive == 1

        case_collectors = case(
            [
                (hidden_conditions, 'Collectors not displayed')
            ],
            else_=SpecifyExport.collectors
        )

        case_collectors_number = case(
            [
                (hidden_conditions, 'Collector number not displayed')
            ],
            else_=SpecifyExport.collector_number
        )

        case_collection_date = case(
            [
                (hidden_conditions, 'Collection date not displayed')
            ],
            else_=SpecifyExport.collection_date
        )

        case_locality = case(
            [
                (hidden_conditions, 'Locality not displayed')
            ],
            else_=SpecifyExport.locality
        )

        search_query = self.session.query(SpecifyExport.catalog_number,
                                          SpecifyExport.determination_history,
                                          SpecifyExport.family1,
                                          SpecifyExport.genus1,
                                          SpecifyExport.genus2,
                                          SpecifyExport.genus3,
                                          case_collectors,
                                          case_collectors_number,
                                          case_collection_date,
                                          case_locality,
                                          SpecifyExport.accompanying_collectors,
                                          SpecifyExport.species1,
                                          SpecifyExport.species2,
                                          SpecifyExport.species3,
                                          SpecifyExport.subspecies1,
                                          SpecifyExport.subspecies2,
                                          SpecifyExport.subspecies3,
                                          SpecifyExport.variety1,
                                          SpecifyExport.variety2,
                                          SpecifyExport.variety3,
                                          SpecifyExport.forma1,
                                          SpecifyExport.forma2,
                                          SpecifyExport.forma3,
                                          SpecifyExport.specimen_notes,
                                          MIFlora2010.plant_id,
                                          MIFlora2010.st,
                                          SpecifyExport.county,
                                          SpecifyExport.latitude,
                                          SpecifyExport.longitude,
                                          SpecifyExport.determiner1,
                                          SpecifyExport.determiner2,
                                          SpecifyExport.determiner3,
                                          SpecifyExport.determination_year1,
                                          SpecifyExport.determination_year2,
                                          SpecifyExport.determination_year3,
                                          SpecifyExport.confidence1,
                                          SpecifyExport.confidence2,
                                          SpecifyExport.confidence3,
                                          SpecifyExport.remarks1,
                                          SpecifyExport.remarks2,
                                          SpecifyExport.remarks3,
                                          SpecifyExport.habitat,
                                          SpecifyExport.herbaria,
                                          MIFlora2010.author)

        search_query = search_query.outerjoin(MIFlora2010, SpecifyExport.plant_id == MIFlora2010.plant_id)

        # Setup our joins.
        # search_query = simple_join_specify_to_miflora(search_query)
        # search_query = join_miflora_to_specify(search_query)
        search_query = join_miflora_to_common_names(search_query)
        search_query = join_miflora_to_synonyms(search_query)
        # search_query = search_query.outerjoin(CommonNames, SpecimenRecords.extra_numerical1 == CommonNames.plant_id)
        # search_query = search_query.outerjoin(Synonyms, SpecimenRecords.extra_numerical1 == Synonyms.plant_id)
        # search_query = search_query.outerjoin(CountySpecimenLookup, SpecimenRecords.county_district ==
        #                                       CountySpecimenLookup.place_name_db)

        # if identity:
        #     search_query=search_query.filter(SpecimenRecords.identity == identity)

        if genus:
            search_query = search_query.filter(SpecifyExport.genus1.ilike('{0}'.format(genus)))

        if collection_year:
            search_query = search_query.filter(SpecifyExport.collection_date.ilike('%{0}%'.format(collection_year)))

        if collector_name:
            search_query = search_query.filter(SpecifyExport.collectors.ilike('%{0}%'.format(collector_name)))

        if common_name:
            search_query = search_query.filter(CommonNames.common_name.ilike('%{0}%'.format(common_name)))

        if collector_number:
            search_query = search_query.filter(SpecifyExport.collector_number == collector_number)

        if family:
            search_query = search_query.filter(SpecifyExport.family1.ilike('{0}'.format(family)))

        if location:
            search_query = search_query.filter(SpecifyExport.locality.ilike('%{0}%'.format(location)))

        if county:
            if ',' in county:
                # Convert from string to list
                county = county.split(',')
            elif type(county) is not list:
                county = [county]
            # TODO: Deal with 'or' in county field
            search_query = search_query.filter(SpecifyExport.county.in_(county))

        if scientific_name:
            search_query = search_query.filter(SpecifyExport.sci_name.ilike('%{0}%'.format(scientific_name)))

        if plant_id:
            search_query = search_query.filter(MIFlora2010.plant_id == plant_id)

        if catalog_number:
            search_query = search_query.filter(or_(SpecifyExport.catalog_number.ilike('{0}'.format(catalog_number)),
                                                   SpecifyExport.catalog_number.ilike('#{0}'.format(catalog_number))))

        search_query = search_query.distinct().order_by(SpecifyExport.catalog_number)

        # Limit our search so we don't return everything at once.  This effectively allows us to paginate the results.
        if n_results > 0:
            search_query = search_query.limit(n_results)

        if offset > 0:
            search_query = search_query.offset(offset)

        return search_query

    def search_specimens_sp(self, n_results=default_n_results, offset=default_offset, common_name="",
                            scientific_name="", genus="", family="", collector_name="", collector_number="",
                            collection_year="", location="", county="", plant_id="", catalog_number=""):

        search_query = self.make_specimen_search_sp(n_results=n_results,
                                                    offset=offset,
                                                    common_name=common_name,
                                                    scientific_name=scientific_name,
                                                    genus=genus,
                                                    family=family,
                                                    collector_name=collector_name,
                                                    collector_number=collector_number,
                                                    collection_year=collection_year,
                                                    location=location,
                                                    county=county,
                                                    plant_id=plant_id,
                                                    catalog_number=catalog_number)

        # Get the search results and pack them into a list of db.core.SpecimenRecord's.
        db_results = search_query.all()

        if db_results:
            records = list()
            for r in db_results:
                records.append(SpecifySearchRecord._make(r))

            return records
        else:
            return None

    def make_specimen_search(self, n_results=default_n_results, offset=default_offset, common_name="",
                             scientific_name="", genus="", family="", collector_name="", collector_number="",
                             collection_year="", location="", county="", identity=""):
        hidden_conditions = or_(MIFlora2010.st == 'E', MIFlora2010.st == 'T')

        case_collectors = case(
            [
                (hidden_conditions, 'Collectors hidden')
            ],
            else_=SpecimenRecords.collectors
        )

        case_collectors_number = case(
            [
                (hidden_conditions, '')
            ],
            else_=SpecimenRecords.collectors_number
        )

        case_collection_date = case(
            [
                (hidden_conditions, 'Collection date hidden')
            ],
            else_=SpecimenRecords.collection_date
        )

        case_locality = case(
            [
                (hidden_conditions, 'Exact localities for State and Federally listed rare plants not displayed.')
            ],
            else_=SpecimenRecords.locality
        )

        search_query = self.session.query(SpecimenRecords.identity,
                                          SpecimenRecords.catalog_number,
                                          FamilyGenus.family,
                                          SpecimenRecords.genus,
                                          case_collectors,
                                          CountySpecimenLookup.place_name,
                                          SpecimenRecords.species_epithet,
                                          SpecimenRecords.infra_rank,
                                          SpecimenRecords.infra_name,
                                          SpecimenRecords.identification_qualifier,
                                          SpecimenRecords.extra_numerical1,
                                          MIFlora2010.st,
                                          SpecimenRecords.county_district,
                                          case_collectors_number,
                                          case_collection_date,
                                          case_locality,
                                          SpecimenRecords.determiner,
                                          SpecimenRecords.determination_history,
                                          SpecimenRecords.accompanying_collectors,
                                          SpecimenRecords.habitat)

        # Setup our joins.
        search_query = search_query.outerjoin(MIFlora2010, SpecimenRecords.extra_numerical1 == MIFlora2010.plant_id)
        search_query = search_query.outerjoin(FamilyGenus, SpecimenRecords.genus == FamilyGenus.genus)
        search_query = search_query.outerjoin(CommonNames, SpecimenRecords.extra_numerical1 == CommonNames.plant_id)
        search_query = search_query.outerjoin(Synonyms, SpecimenRecords.extra_numerical1 == Synonyms.plant_id)
        search_query = search_query.outerjoin(CountySpecimenLookup, SpecimenRecords.county_district ==
                                              CountySpecimenLookup.place_name_db)

        if identity:
            search_query = search_query.filter(SpecimenRecords.identity == identity)

        if genus:
            search_query = search_query.filter(SpecimenRecords.genus.ilike('%{0}%'.format(genus)))

        if collection_year:
            search_query = search_query.filter(SpecimenRecords.collection_date.ilike('%{0}%'.format(collection_year)))

        if collector_name:
            search_query = search_query.filter(SpecimenRecords.collectors.ilike('%{0}%'.format(collector_name)))

        if common_name:
            search_query = search_query.filter(CommonNames.common_name.ilike('%{0}%'.format(common_name)))

        if collector_number:
            search_query = search_query.filter(SpecimenRecords.collectors_number == collector_number)

        if family:
            search_query = search_query.filter(FamilyGenus.family.ilike('%{0}%'.format(family)))

        if location:
            search_query = search_query.filter(SpecimenRecords.locality.ilike('%{0}%'.format(location)))

        if county:
            if type(county) is not list:
                county = [county]

            search_query = search_query.filter(CountySpecimenLookup.place_name.in_(county))

        if scientific_name:
            sci = SpecimenRecords.genus + " " + SpecimenRecords.species_epithet
            search_query = search_query.filter(sci.ilike('%{0}%'.format(scientific_name)))

        search_query = search_query.distinct().order_by(SpecimenRecords.catalog_number)

        # Limit our search so we don't return everything at once.  This effectively allows us to paginate the results.
        if n_results > 0:
            search_query = search_query.limit(n_results)

        if offset > 0:
            search_query = search_query.offset(offset)

        return search_query

    def search_specimens(self, n_results=default_n_results, offset=default_offset, common_name="",
                         scientific_name="", genus="", family="", collector_name="", collector_number="",
                         collection_year="", location="", county="", identity=""):
        search_query = self.make_specimen_search(n_results=n_results,
                                                 offset=offset,
                                                 common_name=common_name,
                                                 scientific_name=scientific_name,
                                                 genus=genus,
                                                 family=family,
                                                 collector_name=collector_name,
                                                 collector_number=collector_number,
                                                 collection_year=collection_year,
                                                 location=location,
                                                 county=county,
                                                 identity=identity)

        # Get the search results and pack them into a list of db.core.SpecimenRecord's.
        db_results = search_query.all()

        if db_results:
            records = list()
            for r in db_results:
                records.append(SpecimenSearchRecord._make(r))

            return records
        else:
            return None

    def specimen_search_count(self, n_results=default_n_results, offset=default_offset, common_name="",
                              scientific_name="", genus="", family="", collector_name="", collector_number="",
                              collection_year="", location="", county=""):
        search_query = self.make_specimen_search(n_results=n_results,
                                                 offset=offset,
                                                 common_name=common_name,
                                                 scientific_name=scientific_name,
                                                 genus=genus,
                                                 family=family,
                                                 collector_name=collector_name,
                                                 collector_number=collector_number,
                                                 collection_year=collection_year,
                                                 location=location,
                                                 county=county)

        return search_query.with_entities(SpecimenRecords.identity).count()

    def search_flora(self, n_results=default_n_results, offset=default_offset, common_name="", scientific_name="",
                     county="", wetness="", w=None, na="", physiognomy="", status="", family="", genus="",
                     coefficient="", plant_id=None):
        search_query = self.make_flora_search(n_results=n_results,
                                              offset=offset,
                                              common_name=common_name,
                                              scientific_name=scientific_name,
                                              county=county,
                                              wetness=wetness,
                                              w=w,
                                              na=na,
                                              physiognomy=physiognomy,
                                              status=status,
                                              family=family,
                                              genus=genus,
                                              coefficient=coefficient,
                                              plant_id=plant_id)

        db_results = search_query.all()

        if db_results:
            records = list()
            for r in db_results:
                i_plant_id = 0
                r_list = list(r)
                r_list.append(self.list_common_names(r[i_plant_id]))
                records.append(FloraSearchRecord._make(r_list))

            return records
        else:
            return None

    def list_common_names(self, plant_id: int) -> list:
        """
        Lists the common names associated with a particular plant ID.

        :param plant_id:
        :return:
        """

        search_query = self.session.query(CommonNames.common_name)
        db_results = search_query.filter(CommonNames.plant_id == plant_id).all()

        # Convert the results into a simple list of strings.
        if db_results:
            return [x[0] for x in db_results]
        else:
            return None

    def list_locations(self, plant_id: int) -> list:
        """
        Lists the locations (county and islands) associated with a plant ID.

        :param plant_id:
        :return:
        """

        search_query = self.session.query(CountySpeciesLookup.place_name)
        search_query = search_query.join(CoSpecies, CountySpeciesLookup.place_name_db == CoSpecies.county)
        search_query = search_query.filter(CoSpecies.plant_id == plant_id)
        db_results = search_query.distinct().order_by(CountySpeciesLookup.island_county_sort,
                                                      CountySpeciesLookup.place_name_type).all()

        # Convert the results into a simple list of strings.
        if db_results:
            return [x[0] for x in db_results]
        else:
            return None

    def list_locations_sp(self, plant_id: int) -> list:
        """
        Lists the locations (county and islands) associated with a plant ID based on records from Specify.

        :param plant_id:
        :return:
        """

        search_query = self.session.query(SpecifyExport.county)
        search_query = search_query.join(MIFlora2010,
                                         func.lower(SpecifyExport.plant_id) == func.lower(MIFlora2010.plant_id))
        search_query = search_query.filter(MIFlora2010.plant_id == plant_id)
        db_results = search_query.distinct().order_by(SpecifyExport.county).all()

        # Convert the results into a simple list of strings.
        if db_results:
            return [x[0] for x in db_results]
        else:
            return None

    def list_synonyms(self, plant_id: int) -> list:
        """
        Returns a list of synonyms for a plant ID.

        :param plant_id:
        :return:
        """

        search_query = self.session.query(Synonyms.syn_species)
        search_query = search_query.filter(Synonyms.plant_id == plant_id)
        db_results = search_query.distinct().order_by(Synonyms.plant_id).all()

        # Convert the results into a simple list of strings.
        if db_results:
            return [x[0] for x in db_results]
        else:
            return None

    def get_primary_image_info(self, plant_id: int) -> ImageRecord:
        """
        Retrieves the 'high-priority' (front page) MI Flora image info record for a given plant ID.

        :param plant_id:
        :return:
        """

        search_query = self.session.query(Images.image_id, Images.jpg_name, Images.plant_id, Images.caption,
                                          Images.photographer)
        search_query = search_query.filter(Images.plant_id == plant_id).filter(Images.priority == 1)
        db_results = search_query.group_by(Images.image_id).all()

        if db_results:
            image_ids = [x.image_id for x in db_results]
            m = max(image_ids)
            i = image_ids.index(m)

            return ImageRecord._make(db_results[i])
        else:
            return None

    def get_all_image_info(self, plant_id: int) -> list:
        """
        Retrieves all MI Flora image info records for a given plant ID.

        :param plant_id:
        :return:
        """

        search_query = self.session.query(Images.image_id, Images.jpg_name, Images.plant_id, Images.caption,
                                          Images.photographer)
        search_query = search_query.filter(Images.plant_id == plant_id)
        db_results = search_query.group_by(Images.image_id).all()

        if db_results:
            records = list()
            for r in db_results:
                r_list = list(r)
                records.append(ImageRecord._make(r_list))
            return records
        else:
            return None

    def get_flora_species_text(self, species_id: int) -> str:
        """
        Returns the HTML text associated with a MI Flora species.
        :param species_id:
        :return:
        """

        search_query = self.session.query(PageTextSpecies.text)
        db_results = search_query.filter(PageTextSpecies.species_id == species_id).one_or_none()

        if db_results:
            return db_results[0]
        else:
            return None

    def get_flora_family_text(self, family_id: str) -> str:
        """
        Returns the HTML text associated with a MI Flora family.
        :param family_id:
        :return:
        """

        search_query = self.session.query(PageTextFamily.text)
        db_results = search_query.filter(PageTextFamily.family_id == family_id).one_or_none()

        if db_results:
            return db_results[0]
        else:
            return None

    def get_flora_genus_text(self, genus_id: str) -> str:
        """
        Returns the HTML text associated with a MI Flora genus.
        :param genus_id:
        :return:
        """

        search_query = self.session.query(PageTextGenus.text)
        db_results = search_query.filter(PageTextGenus.genus_id == genus_id).one_or_none()

        if db_results:
            return db_results[0]
        else:
            return None

    def get_homepage_text(self, page_id: str) -> str:
        """
        Returns the HTML text for a specific page.
        :param page_id:
        :return:
        """
        search_query = self.session.query(HomePagesText.text)
        db_results = search_query.filter(HomePagesText.page_id == page_id).one_or_none()

        if db_results:
            return db_results[0]
        else:
            return None


class SpecimenRecords(MIFLORA_BASE):
    __tablename__ = 'SpecimenRecords'
    __bind_key__ = 'flora_db'

    identity = Column('intIdentity', Integer, nullable=False, primary_key=True)
    catalog_number = Column('strCatalogNumber', String)
    genus = Column('strGenus', String)
    species_epithet = Column('strSpeciesEpithet', String)
    infra_rank = Column('strInfraRank', String)
    infra_name = Column('strInfraName', String)
    identification_qualifier = Column('strIdentificationQualifier', String)
    determiner = Column('strDeterminer', String)
    determination_year = Column('strDeterminationYear', String)
    determination_history = Column('memDeterminationHistory', String)
    collectors = Column('strCollectors', String)
    collectors_number = Column('strCollectorsNumber', String)
    accompanying_collectors = Column('strAccompanyingCollectors', String)
    collection_date = Column('strCollectionDate', String)
    latest_collection_date = Column('strLatestCollectionDate', String)
    county_district = Column('strCountyDistrict', String)
    locality = Column('strLocality', String)
    verbatim_coordinates = Column('strVerbatimCoordinates', String)
    lat_deg = Column('strLatDeg', String)
    lat_min = Column('strLatMin', String)
    lat_sec = Column('strLatSec', String)
    lat_ns = Column('strLatNS', String)
    long_deg = Column('strLongDeg', String)
    long_min = Column('strLongMin', String)
    long_sec = Column('strLongSec', String)
    long_ew = Column('strLongEW', String)
    decimal_latitude = Column('strDecimalLatitude', String)
    decimal_longitude = Column('strDecimalLongitude', String)
    township = Column('strTownship', String)
    range = Column('strRange', String)
    section = Column('strSection', String)
    section_details = Column('strSectionDetails', String)
    habitat = Column('memHabitat', Text)
    specimen_notes = Column('memSpecimenNotes', Text)
    herbaria = Column('strHerbaria', String)
    extra_numerical1 = Column('strExtraNumerical1', Integer)
    date_last_modified = Column('dtmDateLastModified', DateTime)


class SpecifyExport(MIFLORA_BASE):
    __tablename__ = 'tbl_michflora_export'
    __bind_key__ = 'flora_db'

    # identity = Column('intIdentity', Integer, nullable=False, primary_key=True)
    catalog_number = Column('CatalogNumber', String, nullable=False, primary_key=True)
    cataloged_date = Column('CatalogedDate', DateTime)
    determination_history = Column('DetHistory', Text)
    date_last_modified = Column('DateLastModified', DateTime)
    sensitive = Column('Sensitive', Binary)
    donotmap = Column('DoNotMap', Binary)

    determiner1 = Column('DeterminerLastName1', String)
    determination_year1 = Column('DeterminedYear1', String)
    family1 = Column('Family1', String)
    genus1 = Column('Genus1', String)
    species1 = Column('Species1', String)
    subspecies1 = Column('Subspecies1', String)
    variety1 = Column('Variety1', String)
    forma1 = Column('Forma1', String)
    current1 = Column('Current1', Binary)
    confidence1 = Column('Confidence1', String)
    remarks1 = Column('Remarks1', Text)
    determiner2 = Column('DeterminerLastName2', String)
    determination_year2 = Column('DeterminedYear2', String)
    family2 = Column('Family2', String)
    genus2 = Column('Genus2', String)
    species2 = Column('Species2', String)
    subspecies2 = Column('Subspecies2', String)
    variety2 = Column('Variety2', String)
    forma2 = Column('Forma2', String)
    current2 = Column('Current2', Binary)
    confidence2 = Column('Confidence2', String)
    remarks2 = Column('Remarks2', Text)
    determiner3 = Column('DeterminerLastName3', String)
    determination_year3 = Column('DeterminedYear3', String)
    family3 = Column('Family3', String)
    genus3 = Column('Genus3', String)
    species3 = Column('Species3', String)
    subspecies3 = Column('Subspecies3', String)
    variety3 = Column('Variety3', String)
    forma3 = Column('Forma3', String)
    current3 = Column('Current3', Binary)
    confidence3 = Column('Confidence3', String)
    remarks3 = Column('Remarks3', Text)

    collectors = Column('Collectors', Text)
    collector_number = Column('CollectorNumber', String)
    accompanying_collectors = Column('AccompanyingCollectors', String)
    collection_date = Column('CollectionDate', String)
    collection_end_date = Column('CollectionEndDate', String)

    habitat = Column('Habitat', Text)
    country = Column('Country', String)
    state = Column('State', String)
    county = Column('County', String)
    locality = Column('LocalityName', String)
    latitude = Column('Latitude', String)
    longitude = Column('Longitude', String)
    township = Column('Township', String)
    loc_range = Column('Range', String)
    section = Column('Section', String)
    section_part = Column('SectionPart', String)

    specimen_notes = Column('SpecimenNotes', Text)
    curatorial_notes = Column('CuratorialNotes', Text)
    herbaria = Column('Herbaria', Text)
    sci_name = column_property(genus1 + " " + species1)
    plant_id = Column('miflora_plant_id', Integer)


class CountySpecimenLookup(MIFLORA_BASE):
    __tablename__ = 'CountySpecimenLookup'
    __bind_key__ = 'flora_db'

    # This table doesn't actually have any primary keys defined for some reason, so we make the first column primary
    # to make the ORM happy.  As far as I can tell, this column is used like a primary key anyway.
    place_name_db = Column('place_name_db', String, primary_key=True)
    place_name = Column('place_name', String)
    place_name_type = Column('place_name_type', String)
    island_county_sort = Column('island_county_sort', String)


class FamilyGenus(MIFLORA_BASE):
    __tablename__ = 'FamilyGenus'
    __bind_key__ = 'flora_db'

    # This table doesn't actually have any primary keys defined for some reason, so we make the 2nd column primary
    # to make the ORM happy.  As far as I can tell, this column is used like a primary key anyway.
    family = Column('FAMILY', String)
    genus = Column('GENUS', String, primary_key=True)


class CoSpecies(MIFLORA_BASE):
    __tablename__ = 'CoSpecies'
    __bind_key__ = 'flora_db'

    cospid = Column('CoSpID', Integer, nullable=False, primary_key=True)
    plant_id = Column('Plant_ID', Integer)
    species = Column('Species', String)
    county = Column('County', String)
    date_updated = Column('Date_Updated', DateTime)


class CountySpeciesLookup(MIFLORA_BASE):
    __tablename__ = 'CountySpeciesLookup'
    __bind_key__ = 'flora_db'

    id = Column('id', Integer, primary_key=True, nullable=False)
    place_name_db = Column('place_name_db', String)
    place_name = Column('place_name', String)
    place_name_type = Column('place_name_type', String)
    island_county_sort = Column('island_county_sort', String)


class PlantSpecies(MIFLORA_BASE):
    __tablename__ = 'PlantSpecies'
    __bind_key__ = 'flora_db'

    plant_id = Column(Integer, nullable=False, primary_key=True)
    family = Column(String)
    species = Column(String)
    genus = Column(String)
    species_epithet = Column(String)
    date_updated = Column(DateTime)


class PageTextFamily(MIFLORA_BASE):
    __tablename__ = 'PageTextFamily'
    __bind_key__ = 'flora_db'

    family_id = Column('id', String, nullable=False, primary_key=True)
    text = Column('text', Text)


class PageTextGenus(MIFLORA_BASE):
    __tablename__ = 'PageTextGenus'
    __bind_key__ = 'flora_db'

    genus_id = Column('id', String, nullable=False, primary_key=True)
    text = Column('text', Text)


class PageTextSpecies(MIFLORA_BASE):
    __tablename__ = 'PageTextSpecies'
    __bind_key__ = 'flora_db'

    species_id = Column('id', Integer, nullable=False, primary_key=True)
    text = Column('text', Text)


class HomePagesText(MIFLORA_BASE):
    __tablename__ = 'HomePagesText'
    __bind_key__ = 'flora_db'

    page_id = Column('id', String, nullable=False, primary_key=True)
    text = Column('text', Text)


class MIFlora2010(MIFLORA_BASE):
    __tablename__ = 'MIFlora2010'
    __bind_key__ = 'flora_db'

    flora_id = Column('FLORA_ID', Integer, nullable=False, primary_key=True)
    plant_id = Column('PLANT_ID', Integer)
    family_name = Column('FAMILY NAME', String)
    acronym = Column('ACRONYM', String)
    c = Column('C', String)
    scientific_name = Column('SCIENTIFIC NAME', String)
    author = Column('AUTHOR', String)
    n_a = Column('N/A', String)
    st = Column('ST', String)
    w = Column('W', Float)
    wet = Column('WET', String)
    phys = Column('PHYS', String)
    common_name = Column('COMMON NAME', String)
    notes = Column('NOTES', String)
    sci_name_change = Column('SCI NAME (CHANGE)', String)
    fam_common_name = Column('FAM_COMMON_NAME', String)
    ssma_timestamp = Column('SSMA_TIMESTAMP', String, nullable=False)
    date_updated = Column('DATE_UPDATED', DateTime)


class FloraNames(MIFLORA_BASE):
    __tablename__ = 'FloraNames'
    __bind_key__ = 'flora_db'

    id = Column('id', Integer, primary_key=True, nullable=False)
    plant_id = Column('PLANT_ID', Integer)
    scientific_name = Column('Scientific_Name', String)
    c = Column('C', String)
    st = Column('ST', String)
    w = Column('W', Float)
    wet = Column('WET', String)
    phys = Column('PHYS', String)
    na = Column('NA', String)
    syn_species = Column('SYN_SPECIES', String)
    common_name = Column('COMMON_NAME', String)
    family_name = Column('FAMILY_NAME', String)


class CommonNames(MIFLORA_BASE):
    __tablename__ = 'CommonNames'
    __bind_key__ = 'flora_db'

    common_name_id = Column('COMMON_NAME_ID', Integer, nullable=False, primary_key=True)
    plant_id = Column('PLANT_ID', Float)
    common_name = Column('COMMON_NAME', String)
    ssma_timestamp = Column('SSMA_TimeStamp', String, nullable=False)
    date_updated = Column('Date_Updated', DateTime)


class Images(MIFLORA_BASE):
    __tablename__ = 'Images'
    __bind_key__ = 'flora_db'

    image_id = Column('ImageID', Integer, nullable=False, primary_key=True)
    jpg_name = Column('jpgName', String)
    plant_id = Column(Integer)
    caption = Column(String)
    photographer = Column(String)
    priority = Column(TINYINT)
    date_updated = Column(DateTime)
    web_update = Column(Binary)


class ImagesDev(MIFLORA_BASE):
    __tablename__ = 'ImagesDev'
    __bind_key__ = 'flora_db'

    image_id = Column('ImageID', Integer, nullable=False, primary_key=True)
    jpg_name = Column('jpgName', String)
    plant_id = Column(Integer)
    caption = Column(String)
    photographer = Column(String)
    priority = Column(TINYINT)
    date_updated = Column(DateTime)
    web_update = Column(Binary)



class Synonyms(MIFLORA_BASE):
    __tablename__ = 'Synonyms'
    __bind_key__ = 'flora_db'

    synonym_id = Column('SYNONYM_ID', Integer, nullable=False, primary_key=True)
    plant_id = Column('PLANT_ID', Integer)
    syn_species = Column('SYN_SPECIES', String)
    syn_genus = Column('SYN_GENUS', String)
    syn_species_epithet = Column('SYN_SPECIES_EPITHET', String)
    notes = Column('NOTES', String)
    date_updated = Column('Date_Updated', DateTime)

