"""Basic script to validate Thoas config file.  The script checks that all required sections and fields exist, and that
file path locations exist"""

import os.path
from configparser import ConfigParser
from typing import Set


def validate_config(config_parser: ConfigParser) -> None:
    check_required_fields({'GENERAL', 'MONGO DB', 'REFGET DB'}, set(config_parser.sections()))

    def get_section_keys(section: str) -> Set[str]:
        return {key for key, _ in config_parser.items(section=section)}

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
            }
        else:
            required_fields = {
                "production_name",
                "assembly",
                "division",
                "host",
                "port",
                "user",
            }

        check_required_fields(required_fields, get_section_keys(section), section)

    for pathname in ["base_data_path", "grch37_data_path", "classifier_path", "chr_checksums_path",
                     "xref_lod_mapping_file"]:
        check_file_path_exists(pathname, config_parser.get("GENERAL", pathname))


def check_file_path_exists(pathname: str, filepath: str) -> None:
    if not os.path.exists(filepath):
        raise IOError(f"Error validating path provided for {pathname}.  Provided path {filepath} does not exist.")


def check_required_fields(required_fields: Set[str], given_fields: Set[str], section: str = None) -> None:
    missing_fields = required_fields - given_fields
    if missing_fields:
        if section:
            raise IOError(f"Required fields missing from {section} section.  Missing fields are: {missing_fields}")
        # if section parameter is not present, assume this function is validating that all required sections exist in a
        # config file
        raise IOError(f"Required section missing from config file.  Missing sections are: {missing_fields}")
