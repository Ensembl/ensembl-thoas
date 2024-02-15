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


def check_config_validity(config):
    mandatory_fields = [
        "mongo_host",
        "mongo_port",
        "mongo_user",
        "mongo_password",
        "mongo_db",
        "mongo_default_collection",
        "mongo_lookup_service_collection",
        "grpc_host",
        "grpc_port",
    ]
    for mandatory_field in mandatory_fields:
        if not config.get(mandatory_field):
            raise KeyError(
                f"Missing information in configuration file - '{mandatory_field}'"
            )


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
