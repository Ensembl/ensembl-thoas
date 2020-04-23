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
    '''

    def __init__(self, from_file=None):
        self.api_url = 'https://registry.api.identifiers.org/resolutionApi/getResolverDataset'

        if from_file:
            self.id_data = self._load_from_file(from_file)
        else:
            self.id_data = self._load_from_url(self.api_url)

        self.namespace = {}
        self._index_namespaces()

        self.id_substitution = re.compile('\{\$id\}')

    def _load_from_file(self, file):
        'Constructor helper to get JSON from file instead of URL'
        data = None
        with open(file) as raw:
            content = raw.read()
            data = json.loads(content)
        return data

    def _load_from_url(self, url):
        'Get JSON from identifiers.org'

        request = requests.get(url, headers={'Accepts': 'application/json'})
        if request.headers['Content-Type'] == 'application/json':
            return request.json

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
