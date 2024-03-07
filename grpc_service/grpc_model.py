import logging

from ensembl.production.metadata.grpc import ensembl_metadata_pb2

logger = logging.getLogger(__name__)


class GRPC_MODEL:  # pylint: disable=invalid-name
    def __init__(self, grpc_stub):
        self.grpc_stub = grpc_stub

    def get_genome_by_genome_uuid(self, genome_uuid, release_version=None):
        logger.debug(
            "Received RPC for GetGenomeByUUID with genome_uuid: '%s', release: %s",
            genome_uuid,
            release_version,
        )
        request = ensembl_metadata_pb2.GenomeUUIDRequest(
            genome_uuid=genome_uuid, release_version=release_version
        )
        response = self.grpc_stub.GetGenomeByUUID(request)
        return response

    def get_genome_by_keyword(self, keyword, release_version=None):
        logger.debug(
            "Received RPC for GetGenomesByKeyword with keyword: '%s', release: %s",
            keyword,
            release_version,
        )
        request = ensembl_metadata_pb2.GenomeByKeywordRequest(
            keyword=keyword, release_version=release_version
        )
        response = self.grpc_stub.GetGenomesByKeyword(request)
        return response

    def get_genome_by_assembly_acc_id(self, assembly_accession_id):
        logger.debug(
            "Received RPC for GetGenomesByAssemblyAccessionID with assembly_accession_id: '%s'",
            assembly_accession_id,
        )
        request = ensembl_metadata_pb2.AssemblyAccessionIDRequest(
            assembly_accession=assembly_accession_id
        )
        response = self.grpc_stub.GetGenomesByAssemblyAccessionID(request)
        return response

    def get_release_by_genome_uuid(self, genome_uuid):
        request = ensembl_metadata_pb2.ReleaseVersionRequest(genome_uuid=genome_uuid)
        response = self.grpc_stub.GetReleaseVersionByUUID(request)
        return response
