from grpc_service import ensembl_metadata_pb2 as ensembl_metadata_pb2


class GRPC_MODEL:

        def __init__(self, grpc_stub):
            self.grpc_stub = grpc_stub

        def get_genome_by_genome_uuid(self, genome_uuid, release_version=None):
            request = ensembl_metadata_pb2.GenomeUUIDRequest(genome_uuid=genome_uuid, release_version=release_version)
            response = self.grpc_stub.GetGenomeByUUID(request)
            return response


        def get_genome_by_keyword(self, keyword, release_version=None):
            request = ensembl_metadata_pb2.GenomeByKeywordRequest(keyword=keyword, release_version=release_version)
            response = self.grpc_stub.GetGenomesByKeyword(request)
            return response


        def get_genome_by_assembly_acc_id(self, assembly_accession_id):
            request = ensembl_metadata_pb2.AssemblyAccessionIDRequest(assembly_accession=assembly_accession_id)
            response = self.grpc_stub.GetGenomesByAssemblyAccessionID(request)
            return response


        def get_genome_by_genome_name(self, ensembl_name, site_name, release_version=None):
            request = ensembl_metadata_pb2.GenomeNameRequest(ensembl_name=ensembl_name,
                                                             site_name=site_name,
                                                             release_version=release_version)
            response = self.grpc_stub.GetGenomeByName(request)
            return response