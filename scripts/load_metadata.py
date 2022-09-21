import itertools

from mysql.connector import DataError

import common.utils
from common.mongo import MongoDbClient
from common.mysql import MySQLClient


def get_species_names(config):
    """Gets the names of all the species in the config file"""
    all_names = [
        config[section].get("production_name") for section in config.sections()
    ]
    species_names = tuple(species_name for species_name in all_names if species_name)
    if not species_names:
        raise DataError("Could not find the names of any species!")
    return species_names


def load_metadata(config, mongo_client):
    metadata_db_client = MySQLClient(config, "METADATA DB")
    taxon_db_client = MySQLClient(config, "TAXON DB")

    with metadata_db_client.connection.cursor(
        dictionary=True
    ) as meta_cursor, taxon_db_client.connection.cursor(
        dictionary=True
    ) as taxon_cursor:

        species_names = get_species_names(config)

        substitutions = ",".join(["%s"] * len(species_names))
        organism_query = f"""
            SELECT o.scientific_name,
               o.scientific_parlance_name,
               o.organism_id,
               o.taxonomy_id,
               ogm.is_reference
            FROM organism o
                 LEFT JOIN organism_group_member ogm on o.organism_id = ogm.organism_id
            WHERE o.ensembl_name in ({substitutions})
         """

        meta_cursor.execute(organism_query, species_names)
        organism_results = meta_cursor.fetchall()

        assembly_id_query = """
            SELECT a.name
            from assembly a
                     join genome g on a.assembly_id = g.assembly_id
                     join organism o on g.organism_id = o.organism_id
            WHERE o.organism_id = %s"""

        for organism_row in organism_results:
            meta_cursor.execute(assembly_id_query, (organism_row["organism_id"],))
            for assembly_row in meta_cursor.fetchall():
                mongo_client.collection().insert(
                    {
                        "type": "Assembly",
                        "id": assembly_row["name"],
                        "organism_foreign_key": organism_row["organism_id"],
                    }
                )

            species_document = {
                "type": "Species",
                "scientific_name": organism_row["scientific_name"],
                "taxon_id": organism_row["taxonomy_id"],
                "ncbi_common_name": None,
                "alternative_names": [],
                "species_primary_key": organism_row["organism_id"],
            }

            taxon_query = """
                SELECT t.name, t.name_class
                FROM ncbi_taxonomy.ncbi_taxa_name t
                WHERE t.taxon_id = %s
                """

            taxon_cursor.execute(taxon_query, (organism_row["taxonomy_id"],))
            for taxon_row in taxon_cursor.fetchall():
                if taxon_row["name"] and taxon_row["name_class"]:
                    if taxon_row["name_class"] == "genbank common name":
                        species_document["ncbi_common_name"] = taxon_row["name"]
                    elif taxon_row["name_class"] == "common name":
                        species_document["alternative_names"].append(taxon_row["name"])

            organism_document = {
                "type": "Organism",
                "scientific_name": organism_row["scientific_name"],
                "scientific_parlance_name": organism_row["scientific_parlance_name"],
                "is_reference_organism": organism_row["is_reference"]
                if organism_row["is_reference"]
                else False,
                "organism_primary_key": organism_row["organism_id"],
                "species_foreign_key": organism_row["organism_id"],
            }

            # Note that we are creating one organism per species here.  In principle a species can have multiple
            # organisms, but if this ever happens then we should create a new species table in Metadata DB.
            mongo_client.collection().insert_one(organism_document)
            mongo_client.collection().insert_one(species_document)


if __name__ == "__main__":
    ARGS = common.utils.parse_args()

    CONFIG = common.utils.load_config(ARGS.config_file)
    MONGO_COLLECTION = ARGS.mongo_collection
    MONGO_CLIENT = MongoDbClient(CONFIG, MONGO_COLLECTION)
    load_metadata(CONFIG, MONGO_CLIENT)
