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

import gzip

import ijson.backends.python as ijson
# from jsonslicer import JsonSlicer

with gzip.open('../human_genes.json.gz') as file:
    for transcript in ijson.items(file, 'item'):
        print(transcript)
        if int(transcript['start']) > 1000:
            pass


with gzip.open('../human_genes.json.gz') as file:
    for transcript in ijson.items(file, 'item.transcripts.item'):
        if int(transcript['start']) > 1000:
            pass

# with gzip.open('../human_genes.json.gz') as file:
#     for start in JsonSlicer(file, (None, 'transcripts', None, 'start')):
#         # print(thing)
#         if int(start) > 1000:
#             pass
