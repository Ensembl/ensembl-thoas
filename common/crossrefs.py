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


class XrefResolver():
    '''
    Takes Ensembl Xref sources and IDs and supplies URL routes to the
    original data source, example Uniprot Q1242 -> purl.uniprot.org/Q1242

    Setting from_file to a JSON result from identifiers.org will prevent
    network load, and thus demand less traffic

    A secondary load is required to link Ensembl DB names to identifiers.org
    namespace prefixes

    You probably want to use url_from_ens_dbname() to turn Ensembl cross-refs
    into real URLs to the original
    '''

    def __init__(self, from_file=None, mapping_file=None):
        self.api_url = 'https://registry.api.identifiers.org/resolutionApi/getResolverDataset'
        if mapping_file:
            self.mapping_file = mapping_file
        else:
            self.mapping_file = 'docs/xref_LOD_mapping.json'

        if from_file:
            self.id_data = self._load_from_file(from_file)
        else:
            self.id_data = self._load_from_url(self.api_url)
            print('Loaded identifiers.org data via web service')

        self.namespace = {}
        self._index_namespaces()

        self.id_substitution = re.compile(r'{\$id}')

        self.identifiers_mapping = {}
        # Load LOD mappings from file
        with open(self.mapping_file) as file:
            mapping = json.loads(file.read())
            for source in mapping['mappings']:
                if 'ensembl_db_name' in source:
                    self.identifiers_mapping[
                        source['ensembl_db_name'].lower()
                    ] = source
                else:
                    self.identifiers_mapping[
                        source['db_name'].lower()
                    ] = source

        self.info_types = {
            'PROJECTION': 'A reference inferred via homology from an assembly with better annotation coverage',
            'MISC': 'Yes, misc',
            'DIRECT': 'A reference made by an external resource of annotation to an Ensembl feature that Ensembl imports without modification',
            'SEQUENCE_MATCH': 'A reference inferred by the best match of two sequences',
            'INFERRED_PAIR': 'A reference inferred by reference made on a parent feature, e.g. a RefSeq protein Id because the Refseq mRNA accession was assigned to an Ensembl transcript',
            'PROBE': 'Obsolete',
            'UNMAPPED': 'A mapping could be made between Ensembl and this external reference, but the similarity was not high enough',
            'COORDINATE_OVERLAP': 'A reference inferred from annotation of the same locus as a feature in Ensembl. Mostly relevant when comparing annotation between assemblies with different sequences than Ensembl for the same species',
            'CHECKSUM': 'A reference inferred from a sequence checksum match, such as when the sequences are equal',
            'NONE': 'Void',
            'DEPENDENT': 'A reference inferred from a DIRECT reference and the links to other entities made by the external database'
        }

    def _load_from_file(self, file):
        'Constructor helper to get JSON from file instead of URL'
        data = None
        with open(file) as raw:
            content = raw.read()
            data = json.loads(content)
        return data

    def _load_from_url(self, url):
        'Get JSON from identifiers.org'

        response = requests.get(url, headers={'Accepts': 'application/json'})
        if response.status_code != 200:
            raise Exception(f'Unable to load data from Identifiers.org. HTTP response code: {response.status_code}')

        return response.json()

    def _index_namespaces(self):
        '''
        Provide prefix-based indexes for the flat list of entities from
        the identifiers.org api
        '''
        for ns in self.id_data['payload']['namespaces']:
            self.namespace[ns['prefix']] = ns

    def url_generator(self, xref, dbname):
        '''
        Given an xref ID and a dbname, generate a url that resolves to the
        original site page for that xref (fingers crossed)
        '''
        url = None
        if dbname in self.namespace:
            resources = self.namespace[dbname]['resources']
            for i in resources:
                if i['official'] is True:
                    url_base = i['urlPattern']
                    (url, _) = self.id_substitution.subn(xref, url_base)

        else:
            return None
        # some sources seemingly have no official entry.
        # Take the first arbitrarily
        if url is None:
            url_base = resources[0]['urlPattern']
            (url, _) = self.id_substitution.subn(xref, url_base)
        return url

    def source_url_generator(self, dbname):
        '''
        On receipt of a source name (prefix in identifiers.org)
        we then get the official resource and its url.
        Sources have multiple resources in them, which may have
        different URLs. Unhelpful to us but useful generally.
        '''
        url = None
        if dbname in self.namespace:
            resources = self.namespace[dbname]['resources']
            for i in resources:
                if i['official'] is True:
                    url = i['resourceHomeUrl']
        else:
            return None

        # Handle the lack of an official source
        if url is None:
            url = resources[0]['resourceHomeUrl']
        return url

    def translate_dbname(self, dbname):
        '''
        Turn Ensembl DB names into identifiers.org prefixes where possible
        '''
        namespace = self.identifiers_mapping[dbname.lower()]
        if 'id_namespace' in namespace:
            return namespace['id_namespace']

        return None

    def url_from_ens_dbname(self, xref, dbname):
        '''
        Convert Ensembl dbnames and generate an xref URL
        '''
        namespace = self.translate_dbname(dbname)
        if (
                namespace is None and
                'manual_xref_url' in self.identifiers_mapping[dbname.lower()]
        ):
            # Some sources are not in identifiers.org URLs Ensembl needs a URL
            xref_base = self.identifiers_mapping[dbname.lower()]['manual_xref_url']
            return xref_base + xref

        return self.url_generator(xref, namespace)

    def annotate_crossref(self, xref):
        '''
        Called in map functions, to mutate an xref into a better xref
        '''

        xref['url'] = self.url_from_ens_dbname(
            xref['accession_id'],
            xref['source']['id']
        )
        xref['source']['url'] = self.source_url_generator(
            self.translate_dbname(xref['source']['id'])
        )
        xref['assignment_method']['description'] = self.describe_info_type(xref['assignment_method']['type'])
        return xref


    def describe_info_type(self, info_type):
        '''
        Generates a description field for external reference assignment
        info_type is the old core schema name for an enum representing ways
        that an external reference was linked to an Ensembl feature
        '''

        if info_type in  self.info_types:
            return self.info_types[info_type]
        else:
            raise KeyError(f'Illegal xref info_type {info_type} used')