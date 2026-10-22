import logging

logger = logging.getLogger(__name__)


# Note: Copy of GRPC_MODEL class but just uses async channels
class AsyncGrpcModel:
    def __init__(self, grpc_stub, grpc_reflector):
        self.grpc_stub = grpc_stub
        self.reflector = grpc_reflector

    async def get_release_by_genome_uuid(self, genome_uuid):
        request_class = self.reflector.message_class(
            "ensembl_metadata.ReleaseVersionRequest"
        )
        request = request_class(genome_uuid=genome_uuid)
        return await self.grpc_stub.GetReleaseVersionByUUID(request)
