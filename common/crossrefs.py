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

import json
import re

import requests


class XrefResolver:
    """
    Takes Ensembl Xref sources and IDs and supplies URL routes to the
    original data source, example Uniprot Q1242 -> purl.uniprot.org/Q1242

    Setting from_file to a JSON result from identifiers.org will prevent
    network load, and thus demand less traffic

    A secondary load is required to link Ensembl DB names to identifiers.org
    namespace prefixes

    You probably want to use find_url_using_ens_xref_db_name() to turn Ensembl cross-refs
    into real URLs to the original
    """

    def __init__(
        self, from_file=None, internal_mapping_file="docs/xref_LOD_mapping.json"
    ):

        self.internal_mapping_file = internal_mapping_file
        self.identifiers_org_api_url = (
            "https://registry.api.identifiers.org/resolutionApi/getResolverDataset"
        )

        if from_file:
            self.identifiers_org_data = self._load_from_file(from_file)
        else:
            self.identifiers_org_data = self._load_from_url(
                self.identifiers_org_api_url
            )
            print("Loaded identifiers.org data via web service")

        self.id_org_indexed = {}
        self._index_identifiers_org_data()

        self.id_substitution = re.compile(r"{\$id}")

        self.internal_mapping_file_indexed = {}
        # Load LOD mappings from file
        with open(self.internal_mapping_file, encoding="UTF-8") as file:
            mapping = json.loads(file.read())
            for source in mapping["mappings"]:
                if "ensembl_db_name" in source:
                    self.internal_mapping_file_indexed[
                        source["ensembl_db_name"].lower()
                    ] = source
                else:
                    self.internal_mapping_file_indexed[
                        source["db_name"].lower()
                    ] = source

        self.info_types = {
            "PROJECTION": "A reference inferred via homology from an assembly with better annotation coverage",
            "MISC": "Yes, misc",
            "DIRECT": "A reference made by an external resource of annotation to an Ensembl feature that Ensembl imports without modification",
            "SEQUENCE_MATCH": "A reference inferred by the best match of two sequences",
            "INFERRED_PAIR": "A reference inferred by reference made on a parent feature, e.g. a RefSeq protein Id because the Refseq mRNA accession was assigned to an Ensembl transcript",
            "PROBE": "Obsolete",
            "UNMAPPED": "A mapping could be made between Ensembl and this external reference, but the similarity was not high enough",
            "COORDINATE_OVERLAP": "A reference inferred from annotation of the same locus as a feature in Ensembl. Mostly relevant when comparing annotation between assemblies with different sequences than Ensembl for the same species",
            "CHECKSUM": "A reference inferred from a sequence checksum match, such as when the sequences are equal",
            "NONE": "Void",
            "DEPENDENT": "A reference inferred from a DIRECT reference and the links to other entities made by the external database",
        }

    def _load_from_file(self, file):
        "Constructor helper to get JSON from file instead of URL"
        data = None
        with open(file, encoding="UTF-8") as raw:
            content = raw.read()
            data = json.loads(content)
        return data

    def _load_from_url(self, url):
        "Get JSON from identifiers.org"

        response = requests.get(url, headers={"Accepts": "application/json"})
        if response.status_code != 200:
            raise Exception(
                f"Unable to load data from Identifiers.org. HTTP response code: {response.status_code}"
            )

        return response.json()

    def _index_identifiers_org_data(self):
        """
        Provide prefix-based indexes for the flat list of entities from
        the identifiers.org api
        """
        for namespace in self.identifiers_org_data["payload"]["namespaces"]:
            self.id_org_indexed[namespace["prefix"]] = namespace

    def generate_url_from_id_org_data(self, xref_acc_id, id_org_ns_prefix):
        """
        Given an xref ID and a identifiers.org Namespace Prefix, generate a url that resolves to the
        original site page for that xref (fingers crossed)
        """
        url = None
        if id_org_ns_prefix in self.id_org_indexed:
            resources = self.id_org_indexed[id_org_ns_prefix]["resources"]
            for i in resources:
                if i["official"] is True:
                    url_base = i["urlPattern"]
                    (url, _) = self.id_substitution.subn(xref_acc_id, url_base)

        else:
            print(f"*** {id_org_ns_prefix} namespace not in identifiers.org ***")
            return None
        # some sources seemingly have no official entry.
        # Take the first arbitrarily
        if url is None:
            url_base = resources[0]["urlPattern"]
            (url, _) = self.id_substitution.subn(xref_acc_id, url_base)
        return url

    def source_information_retriever(self, dbname, field):
        """
        On receipt of a source name (prefix in identifiers.org)
        we then get the official resource and its fields(url or description etc).
        Sources have multiple resources in them, which may have
        different field values. Unhelpful to us but useful generally.
        """

        if dbname is None or field is None:
            return None

        data = None
        if dbname in self.id_org_indexed:
            resources = self.id_org_indexed[dbname]["resources"]
            for i in resources:
                if i["official"] is True:
                    data = i[field]
        else:
            return None

        # Handle the lack of an official source
        if data is None:
            data = resources[0][field]
        return data

    def translate_xref_db_name_to_id_org_ns_prefix(self, xref_db_name):
        """
        Turn Ensembl DB names into identifiers.org prefixes where possible
        """

        if xref_db_name is None:
            return None

        if xref_db_name.lower() in self.internal_mapping_file_indexed:
            mapping_entry = self.internal_mapping_file_indexed[xref_db_name.lower()]
            if "id_namespace" in mapping_entry:
                return mapping_entry["id_namespace"]
            print(
                f"*** No id_namespace for {xref_db_name.lower()} in the internal mapping file ***"
            )
        else:
            print(f"*** {xref_db_name.lower()} not in the internal mapping file ***")

        return None

    def find_url_using_ens_xref_db_name(self, xref_acc_id, xref_db_name):
        """
        Convert Ensembl xref_db_name and generate an xref URL
        """

        if xref_acc_id is None or xref_db_name is None:
            return None

        # Find identifiers.org prefix for a given ensembl xref_db_name
        id_org_ns_prefix = self.translate_xref_db_name_to_id_org_ns_prefix(xref_db_name)

        # If there is no id_org_ns_prefix defined in mapping file but manual_xref_url is defined,
        # use this manual_xref_url to generate URL.
        if (
            id_org_ns_prefix is None
            and xref_db_name.lower() in self.internal_mapping_file_indexed
            and "manual_xref_url"
            in self.internal_mapping_file_indexed[xref_db_name.lower()]
        ):
            # Some sources are not in identifiers.org URLs Ensembl needs a URL
            xref_base = self.internal_mapping_file_indexed[xref_db_name.lower()][
                "manual_xref_url"
            ]
            return xref_base + xref_acc_id

        # Now get the URL from identifiers.org using the id_org_ns_prefix and xref_id
        url = self.generate_url_from_id_org_data(xref_acc_id, id_org_ns_prefix)

        return url

    def annotate_crossref(self, xref):
        """
        Called in map functions, to mutate an xref into a better xref
        """

        try:
            xref["url"] = self.find_url_using_ens_xref_db_name(
                xref["accession_id"], xref["source"]["id"]
            )
            xref["source"]["url"] = self.source_information_retriever(
                self.translate_xref_db_name_to_id_org_ns_prefix(xref["source"]["id"]),
                "resourceHomeUrl",
            )
            xref["assignment_method"]["description"] = self.describe_info_type(
                xref["assignment_method"]["type"]
            )
            return xref
        except:
            # probably log the error somewhere; just don't send it to the client
            return None

    def describe_info_type(self, info_type):
        """
        Generates a description field for external reference assignment
        info_type is the old core schema name for an enum representing ways
        that an external reference was linked to an Ensembl feature
        """

        if info_type not in self.info_types:
            raise KeyError(f"Illegal xref info_type {info_type} used")
        return self.info_types[info_type]
