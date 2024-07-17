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

import logging
from typing import List

from graphql import GraphQLResolveInfo

logger = logging.getLogger(__name__)


def check_config_validity(config):
    mandatory_fields = [
        "mongo_host",
        "mongo_port",
        "mongo_user",
        "mongo_password",
        "mongo_default_db",
        "grpc_host",
        "grpc_port",
    ]
    for mandatory_field in mandatory_fields:
        if not config.get(mandatory_field):
            raise KeyError(
                f"Missing information in configuration file - '{mandatory_field}'"
            )


def process_release_version(grpc_response):
    """
    Processes the release version from the gRPC response and formats it for use as a database name.

    This function extracts the release version from the provided gRPC response, replaces any dots ('.')
    with underscores ('_') to avoid pymongo.errors.InvalidName errors, and returns a formatted database
    name string.

    Args:
        grpc_response: The gRPC response object containing the release version.

    Returns:
        str: A formatted string suitable for use as a database name, prefixed with 'release_'.
    """
    logger.debug("[get_database_conn] grpc_response: %s", grpc_response)
    # replacing '.' with '_' to avoid
    # "pymongo.errors.InvalidName: database names cannot contain the character '.'" error ¯\_(ツ)_/¯
    release_version = str(grpc_response.release_version).replace(".", "_")
    logger.debug("[get_database_conn] release_version: %s", release_version)
    return "release_" + release_version


def get_ensembl_metadata_api_version():
    """
    Get the Metadata API tag from requirement.txt file
    """
    version = "unknown"  # default version
    with open("requirements.txt", "r", encoding="UTF-8") as file:
        lines = file.readlines()
        for line in lines:
            if "ensembl-metadata-api" in line:
                # Extract the tag part from the line
                version = line.strip().split("@")[-1]
                break
    return version


def check_requested_fields(info: GraphQLResolveInfo, fields: List[str]) -> List[bool]:
    """
    Check if specific fields are requested in the GraphQL query.

    Args:
        info (ResolveInfo): The GraphQL resolve information containing query details.
        fields (List[str]): A list of field names to check for in the query.

    Returns:
        List[bool]: A list of booleans indicating whether each field is present in the query.

    Usage example:
        fields_to_check = ["assembly", "dataset"]
        is_assembly_present, is_dataset_present = check_requested_fields(info, fields_to_check)
    """
    requested_fields = [
        field.name.value for field in info.field_nodes[0].selection_set.selections
    ]
    return [field in requested_fields for field in fields]
