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

from os import access, R_OK
from os.path import isfile, isdir
from configparser import ConfigParser
from typing import Set


def validate_config(config_parser: ConfigParser) -> None:
    """Basic function to validate Thoas config file.  The script checks that all required sections and fields exist, and
     that file path locations exist"""
    check_required_fields({'GENERAL', 'MONGO DB', 'REFGET DB'}, set(config_parser.sections()))

    for section in config_parser.sections():
        if section == "GENERAL":
            required_fields = {
                "base_data_path",
                "grch37_data_path",
                "release",
                "classifier_path",
                "chr_checksums_path",
                "xref_lod_mapping_file",
                "log_faulty_urls"
            }
        elif section in {"MONGO DB", "REFGET DB"}:
            required_fields = {
                "host",
                "port",
                "user",
                "password",
                "db"
            }
        else:
            required_fields = {
                "production_name",
                "assembly",
                "division",
                "host",
                "port",
                "user",
                "database"
            }

        section_keys = {key for key, _ in config_parser.items(section=section)}

        check_required_fields(required_fields, section_keys, section)

    for pathname in ["base_data_path", "grch37_data_path", "classifier_path", "chr_checksums_path",
                     "xref_lod_mapping_file"]:
        check_path_exists(pathname, config_parser.get("GENERAL", pathname))


def check_path_exists(pathname: str, path: str) -> None:
    assert (isfile(path) or isdir(path)) and access(path, R_OK), \
        f"Error validating path provided for {pathname}.  Provided path {path} does not exist or isn't readable."


def check_required_fields(required_fields: Set[str], given_fields: Set[str], section: str = None) -> None:
    missing_fields = required_fields - given_fields
    if missing_fields:
        if section:
            raise IOError(f"Required fields missing from {section} section.  Missing fields are: {missing_fields}")
        # if section parameter is not present, assume this function is validating that all required sections exist in a
        # config file
        raise IOError(f"Required section missing from config file.  Missing sections are: {missing_fields}")
