"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

from typing import Optional, Dict

import grpc
from graphql import GraphQLError


class DatabaseNotFoundError(GraphQLError):
    """
    Custom error to be raised if database is not found
    """

    def __init__(self, db_name: str):
        self.extensions = {"code": "DATABASE_NOT_FOUND"}
        message = f"Failed to find database: {db_name}"
        super().__init__(message, extensions=self.extensions)


class CollectionNotFoundError(GraphQLError):
    """
    Custom error to be raised if collection is not found
    """

    def __init__(self, collection_name: str):
        self.extensions = {"code": "COLLECTION_NOT_FOUND"}
        message = f"Failed to find collection: {collection_name}"
        super().__init__(message, extensions=self.extensions)


class FieldNotFoundError(GraphQLError):
    """
    Custom error to be raised if a field cannot be found by id
    """

    def __init__(self, field_type: str, key_dict: Dict[str, str]):
        self.extensions = {"code": f"{field_type.upper()}_NOT_FOUND"}
        ids_string = ", ".join([f"{key}={val}" for key, val in key_dict.items()])
        message = f"Failed to find {field_type} with ids: {ids_string}"
        self.extensions.update(key_dict)
        super().__init__(message, extensions=self.extensions)


class FeatureNotFoundError(FieldNotFoundError):
    """
    Custom error to be raised if a gene or transcript cannot be found by id
    """

    def __init__(
        self,
        feature_type: str,
        bySymbol: Optional[Dict[str, str]] = None,
        byId: Optional[Dict[str, str]] = None,
    ):
        if bySymbol:
            super().__init__(
                feature_type,
                {"symbol": bySymbol["symbol"], "genome_id": bySymbol["genome_id"]},
            )
        if byId:
            super().__init__(
                feature_type,
                {"stable_id": byId["stable_id"], "genome_id": byId["genome_id"]},
            )


class GeneNotFoundError(FeatureNotFoundError):
    """
    Custom error to be raised if gene is not found
    """

    def __init__(
        self,
        by_symbol: Optional[Dict[str, str]] = None,
        by_id: Optional[Dict[str, str]] = None,
    ):
        super().__init__("gene", by_symbol, by_id)


class TranscriptNotFoundError(FeatureNotFoundError):
    """
    Custom error to be raised if transcript is not found
    """

    def __init__(
        self,
        by_symbol: Optional[Dict[str, str]] = None,
        by_id: Optional[Dict[str, str]] = None,
    ):
        super().__init__("transcript", by_symbol, by_id)


class ProductNotFoundError(FieldNotFoundError):
    """
    Custom error to be raised if product is not found
    """

    def __init__(self, product_id: str, genome_id: str):
        super().__init__("product", {"product_id": product_id, "genome_id": genome_id})


class RegionFromSliceNotFoundError(FieldNotFoundError):
    """Custom error to be raised if we can't find the region for a slice"""

    def __init__(self, region_id: str):
        super().__init__("region", {"region_id": region_id})


class RegionNotFoundError(FieldNotFoundError):
    """
    Custom error to be raised if region is not found
    """

    def __init__(self, genome_id: str, name: str):
        super().__init__("region", {"genome_id": genome_id, "name": name})


class AssemblyNotFoundError(FieldNotFoundError):
    """
    Custom error to be raised in assembly is not found
    """

    def __init__(self, assembly_id: str):
        super().__init__("assembly", {"assembly_id": assembly_id})


class RegionsFromAssemblyNotFound(FieldNotFoundError):
    """
    Custom error to be raised if we can't find the regions for an assembly
    """

    def __init__(self, assembly_id):
        super().__init__("regions", {"assembly_id": assembly_id})


class OrganismFromAssemblyNotFound(FieldNotFoundError):
    """
    Custom error to be raised if we can't find the organism for an assembly
    """

    def __init__(self, organism_id):
        super().__init__("organism", {"organism_id": organism_id})


class AssembliesFromGenomeNotFound(FieldNotFoundError):
    """
    Custom error to be raised if we can't find the assemblies for a genome
    """

    def __init__(self, assembly_id):
        super().__init__("assemblies", {"assembly_id": assembly_id})


class AssembliesFromOrganismNotFound(FieldNotFoundError):
    """
    Custom error to be raised if we can't find the assemblies for an organism
    """

    def __init__(self, organism_id):
        super().__init__("assemblies", {"organism_id": organism_id})


class SpeciesFromOrganismNotFound(FieldNotFoundError):
    """
    Custom error to be raised if we can't find the species for an organism
    """

    def __init__(self, species_id):
        super().__init__("species", {"species_id": species_id})


class OrganismsFromSpeciesNotFound(FieldNotFoundError):
    """
    Custom error to be raised if we can't find the organisms for a species
    """

    def __init__(self, species_id):
        super().__init__("organisms", {"species_id": species_id})


class SliceLimitExceededError(GraphQLError):
    """
    Custom error to be raised if number of slice results exceeds limit
    """

    extensions = {"code": "SLICE_RESULT_LIMIT_EXCEEDED"}

    def __init__(self, max_results_size: int):
        message = f"Slice query met size limit of {max_results_size}"
        super().__init__(message, extensions=self.extensions)


class InputFieldArgumentNumberError(GraphQLError):
    """
    Custom error to be raised if wrong number of input arguments are sent
    """

    def __init__(self, number_of_input_arguments: int):
        message = f"Set {number_of_input_arguments} input argument(s)"
        super().__init__(message)


class GenomeNotFoundError(FieldNotFoundError):
    """
    Custom error to be raised if product is not found
    """

    def __init__(self, by_genome_uuid):
        super().__init__("genome", by_genome_uuid)


class MissingArgumentException(GraphQLError):
    """
    Exception raised when a required argument is missing.
    """

    def __init__(self, message: str):
        """Initializes a MissingArgumentException instance.

        Args:
            message: The error message describing the missing argument.
        """
        super().__init__(message)


class FailedToConnectToGrpc(GraphQLError):
    """
    Exception raised when there is gRPC connection issue.
    """

    def __init__(self, message: str):
        """Initializes a FailedToConnectToGrpc instance.

        Args:
            message: The error message describing the issue.
        """
        self.extensions = {"code": "SERVER_CONNECTION_FAILED"}
        super().__init__(message, extensions=self.extensions)
