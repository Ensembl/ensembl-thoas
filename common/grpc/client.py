import grpc
from common.grpc import ensembl_metadata_pb2_grpc as ensembl_metadata_pb2_grpc, \
    ensembl_metadata_pb2 as ensembl_metadata_pb2


class GRPCClient(object):
    """
    Client for gRPC functionality
    """
    def __init__(self, config):

        host = config.get("GRPC", "host")
        port = config.get("GRPC", "port")

        # instantiate a channel
        self.channel = grpc.insecure_channel(
            '{}:{}'.format(host, port), options=(('grpc.enable_http_proxy', 0),))

        # bind the client and the server
        self.stub = ensembl_metadata_pb2_grpc.EnsemblMetadataStub(self.channel)


    def get_genome_by_genome_uuid(self, genome_uuid, release_version=None):
        request = ensembl_metadata_pb2.GenomeUUIDRequest(genome_uuid=genome_uuid, release_version=release_version)
        response = self.stub.GetGenomeByUUID(request)
        return response

    def get_genome_by_keyword(self, keyword, release_version=None):
        request = ensembl_metadata_pb2.GenomeByKeywordRequest(keyword=keyword, release_version=release_version)
        response = self.stub.GetGenomesByKeyword(request)
        return response

    def get_genome_by_assembly_acc_id(self, assembly_accession_id):
        request = ensembl_metadata_pb2.AssemblyAccessionIDRequest(assembly_accession=assembly_accession_id)
        response = self.stub.GetGenomesByAssemblyAccessionID(request)
        return response

    def get_genome_by_genome_name(self, ensembl_name, site_name, release_version=None):
        request = ensembl_metadata_pb2.GenomeNameRequest(ensembl_name=ensembl_name,
                                                         site_name=site_name,
                                                         release_version=release_version)
        response = self.stub.GetGenomeByName(request)
        return response