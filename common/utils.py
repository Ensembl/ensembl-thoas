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

from graphql import GraphQLResolveInfo, FieldNode

logger = logging.getLogger(__name__)


def check_config_validity(config):
    mandatory_fields = [
        "MONGO_HOST",
        "MONGO_PORT",
        "MONGO_USER",
        "MONGO_PASSWORD",
        "MONGO_DEFAULT_DB",
        "GRPC_HOST",
        "GRPC_PORT",
        "REDIS_HOST",
        "REDIS_PORT",
        "REDIS_EXPIRY_SECONDS",
        "GRPC_ENABLE_CACHE",
    ]
    for mandatory_field in mandatory_fields:
        if not config.get(mandatory_field):
            raise KeyError(
                f"Missing information in configuration file - '{mandatory_field}'"
            )


def release_database_name(release):
    """
    Formats a release version or release name for use as a MongoDB database name.

    This function replaces any dots ('.') with underscores ('_') to avoid
    pymongo.errors.InvalidName errors, and returns a formatted database name string.
    For example, "110.1" becomes "release_110_1" and "1" becomes "release_1".
    It only formats the name; it does not check whether the database exists.

    Args:
        release: The release version or release name from the MongoDB mapping,
            or an explicitly supplied release version.

    Returns:
        str: A formatted string suitable for use as a database name, prefixed with 'release_'.
    """
    logger.debug("[release_database_name] release: %s", release)
    # replacing '.' with '_' to avoid
    # "pymongo.errors.InvalidName: database names cannot contain the character '.'" error ¯\_(ツ)_/¯
    formatted_release = str(release).replace(".", "_")
    logger.debug("[release_database_name] formatted_release: %s", formatted_release)
    return "release_" + formatted_release


def check_requested_fields(info: GraphQLResolveInfo, fields: List[str]) -> List[bool]:
    """
    Check if specific fields are requested in the GraphQL query.

    Args:
        info (GraphQLResolveInfo): The GraphQL resolve information containing query details.
        fields (List[str]): A list of field names to check for in the query.

    Returns:
        List[bool]: A list of booleans indicating whether each field is present in the query.

    Usage example:
        fields_to_check = ["assembly", "dataset"]
        is_assembly_present, is_dataset_present = check_requested_fields(info, fields_to_check)
    """
    requested_fields = []
    if info.field_nodes:
        selection_set = info.field_nodes[0].selection_set
        if selection_set and selection_set.selections:
            for field in selection_set.selections:
                if isinstance(field, FieldNode) and field.name and field.name.value:
                    requested_fields.append(field.name.value)

    return [field in requested_fields for field in fields]
