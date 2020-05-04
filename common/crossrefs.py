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
import requests
import re


class xref_resolver(object):
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
        with open(self.mapping_file) as mapping_file:
            mapping = json.loads(mapping_file.read())
            for source in mapping['mappings']:
                if 'ensembl_db_name' in source:
                    self.identifiers_mapping[
                        source['ensembl_db_name'].lower()
                    ] = source
                else:
                    self.identifiers_mapping[
                        source['db_name'].lower()
                    ] = source

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
        if (response.status_code == 200):
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
        if dbname in self.namespace:
            resources = self.namespace[dbname]['resources']
            for i in resources:
                if i['official'] is True:
                    url_base = i['urlPattern']
                    (url, count) = self.id_substitution.subn(xref, url_base)
                    return url
        else:
            return None

    def source_url_generator(self, dbname):
        '''
        On receipt of a source name (prefix in identifiers.org)
        we then get the official resource and its url.
        Sources have multiple resources in them, which may have
        different URLs. Unhelpful to us but useful generally.
        '''
        if dbname in self.namespace:
            resources = self.namespace[dbname]['resources']
            for i in resources:
                if i['official'] is True:
                    return i['resourceHomeUrl']
        else:
            return None

    def translate_dbname(self, dbname):
        '''
        Turn Ensembl DB names into identifiers.org prefixes where possible
        '''
        namespace = self.identifiers_mapping[dbname.lower()]
        if 'id_namespace' in namespace:
            return namespace['id_namespace']
        else:
            return None

    def url_from_ens_dbname(self, xref, dbname):
        '''
        Convert Ensembl dbnames and generate a URL
        '''
        namespace = self.translate_dbname(dbname)
        return self.url_generator(xref, namespace)

    def annotate_crossref(self, xref):
        '''
        Called in map functions, to mutate an xref into a better xref
        '''

        xref['url'] = self.url_from_ens_dbname(
            xref['id'],
            xref['source']['id']
        )
        url = self.source_url_generator(
            self.translate_dbname(xref['source']['id'])
        )
        xref['source']['url'] = url
        return xref
