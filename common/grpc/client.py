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
            '{}:{}'.format(host, port))

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

    def get_genome_by_assembly_acc_id(self, genome_uuid):
        request = ensembl_metadata_pb2.GenomeUUIDRequest(genome_uuid=genome_uuid)
        print(f'{request}')
        response = self.stub.GetGenomeByUUID(request)
        print(f'{response}')
        return response

    def get_genome_by_genome_name(self, genome_uuid):
        request = ensembl_metadata_pb2.GenomeUUIDRequest(genome_uuid=genome_uuid)
        print(f'{request}')
        response = self.stub.GetGenomeByUUID(request)
        print(f'{response}')
        return response