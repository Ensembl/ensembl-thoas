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
import re
import json

class TSL:
    regex = re.compile("tsl(\d+|NA)")
    definitions = {
        "1" : "All splice junctions of the transcript are supported by at least one non-suspect mRNA",
        "2" : "The best supporting mRNA is flagged as suspect or the support is from multiple ESTs",
        "3" : "The only support is from a single EST",
        "4" : "The best supporting EST is flagged as suspect",
        "5" : "No single transcript supports the model structure",
        "NA" : "The transcript was not analysed"
        }

    def __init__(self, str):
        self._str = str.strip()
        self.value = None
        self.label = None
        self.definition = None
        self.description = None

    def parse_input(self):
        tsl_matches = self.regex.match(self._str)
        if tsl_matches:
            self.value = tsl_matches.group(1)
            self.label = f'TSL:{self.value}'
            self.definition = self.definitions[self.value]
            self.description = ""
            return True
        return False

    def to_json(self):
        tsl_dict = self.__dict__
        del tsl_dict['_str']
        return tsl_dict

class APPRIS:
    regex = re.compile("(principal|alternative)(\d+)")
    appris_qualifiers = {

    }
    definitions = {
        "principal1" : "Transcript(s) expected to code for the main functional isoform based solely on the core modules in the APPRIS",
        "principal2" : "Two or more of the CDS variants as \"candidates\" to be the principal variant.",
        "principal3" : "Lowest CCDS identifier as the principal variant",
        "principal4" : "Longest CCDS isoform as the principal variant",
        "principal5" : "The longest of the candidate isoforms as the principal variant",
        "alternative1" : "Candidate transcript(s) models that are conserved in at least three tested species",
        "alternative2" : "Candidate transcript(s) models that appear to be conserved in fewer than three tested species"
        }

    def __init__(self, str):
        self._str = str.strip()
        self.value = None
        self.label = None
        self.definition = None
        self.description = None

    def parse_input(self):
        appris_matches = self.regex.match(self._str)
        if appris_matches:
            self.value = f'{appris_matches.groups()[0]}{appris_matches.groups()[1]}'
            self.label = f'APPRIS {appris_matches.groups()[0]}:{appris_matches.groups()[1]}'
            self.definition = self.definitions[self.value]
            self.description = ""
            return True
        return False

    def to_json(self):
        appris_dict = self.__dict__
        del appris_dict['_str']
        return appris_dict

class MANE:
    base_url = "https://www.ncbi.nlm.nih.gov/nuccore/" # Not sure what base_url should be
    mane_qualifiers = {
        "select" : {
            "label" : "MANE Select",
            "definition" : "The MANE Select is a default transcript per human gene that is representative of biology, well-supported, expressed and highly-conserved."
            },
        "plus_clinical" : {
            "label" : "MANE Plus Clinical",
            "definition" : "Transcripts in the MANE Plus Clinical set are additional transcripts per locus necessary to support clinical variant reporting"
            }
        }

    def __init__(self, value, ncbi_id):
        self.value = value.strip()
        self.label = self.mane_qualifiers[self.value]['label']
        self.definition = self.mane_qualifiers[self.value]['definition']
        self.description = ''
        if ncbi_id:
            self.ncbi_transcript = {
               "id" : ncbi_id,
               "url" : f'{self.base_url}{ncbi_id}'
            }
        else:
            ncbi_transcript = {}

    def to_json(self):
        mane_dict = self.__dict__
        return mane_dict
