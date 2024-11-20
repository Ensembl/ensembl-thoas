import logging

logger = logging.getLogger(__name__)


class GRPC_MODEL:  # pylint: disable=invalid-name
    def __init__(self, grpc_stub, grpc_reflector):
        self.grpc_stub = grpc_stub
        self.reflector = grpc_reflector

    def get_genome_by_genome_uuid(self, genome_uuid, release_version=None):
        logger.debug(
            "Received RPC for GetGenomeByUUID with genome_uuid: '%s', release: %s",
            genome_uuid,
            release_version,
        )
        request_class = self.reflector.message_class(
            "ensembl_metadata.GenomeUUIDRequest"
        )

        request = request_class(
            genome_uuid=genome_uuid, release_version=release_version
        )
        response = self.grpc_stub.GetGenomeByUUID(request)

        return response

    def get_genome_by_specific_keyword(
        self,
        tolid=None,
        assembly_accession_id=None,
        assembly_name=None,
        ensembl_name=None,
        common_name=None,
        scientific_name=None,
        scientific_parlance_name=None,
        species_taxonomy_id=None,
        release_version=None,
    ):
        logger.debug(
            "Received RPC for GetGenomesBySpecificKeyword with tolid: '%s', assembly_accession_id: '%s', "
            "assembly_name: '%s', ensembl_name: '%s', common_name: '%s', scientific_name: '%s', "
            "scientific_parlance_name: '%s', species_taxonomy_id: '%s', release: %s",
            tolid,
            assembly_accession_id,
            assembly_name,
            ensembl_name,
            common_name,
            scientific_name,
            scientific_parlance_name,
            species_taxonomy_id,
            release_version,
        )

        request_class = self.reflector.message_class(
            "ensembl_metadata.GenomeBySpecificKeywordRequest"
        )

        request = request_class(
            tolid=tolid,
            assembly_accession_id=assembly_accession_id,
            assembly_name=assembly_name,
            ensembl_name=ensembl_name,
            common_name=common_name,
            scientific_name=scientific_name,
            scientific_parlance_name=scientific_parlance_name,
            species_taxonomy_id=species_taxonomy_id,
            release_version=release_version,
        )
        response = self.grpc_stub.GetGenomesBySpecificKeyword(request)
        return response

    def get_datasets_list_by_uuid(self, genome_uuid, release_version=None):
        logger.debug(
            "Received RPC for GetDatasetsListByUUID with genome_uuid: '%s', release: %s",
            genome_uuid,
            release_version,
        )
        request_class = self.reflector.message_class("ensembl_metadata.DatasetsRequest")

        request = request_class(
            genome_uuid=genome_uuid, release_version=release_version
        )
        response = self.grpc_stub.GetDatasetsListByUUID(request)
        return response

    def get_release_by_genome_uuid(self, genome_uuid):
        request_class = self.reflector.message_class(
            "ensembl_metadata.ReleaseVersionRequest"
        )

        request = request_class(genome_uuid=genome_uuid)
        response = self.grpc_stub.GetReleaseVersionByUUID(request)
        return response
