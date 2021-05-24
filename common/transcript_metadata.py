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

    def toJson(self):
        tsl_dict = self.__dict__
        del tsl_dict['_str']
        return tsl_dict