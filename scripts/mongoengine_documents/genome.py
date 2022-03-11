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

from mongoengine import IntField, StringField, BooleanField

from scripts.mongoengine_documents.base import ThoasDocument


class Assembly(ThoasDocument):
    type = StringField(default="Assembly")
    default = BooleanField()
    assembly_id = StringField()
    name = StringField()
    accession_id = StringField()
    accessioning_body = StringField()
    species = StringField()


class Species(ThoasDocument):
    type = StringField(default="Species")
    species_id = StringField()
    scientific_name = StringField()
    taxon_id = IntField()


class Genome(ThoasDocument):
    type = StringField(default="Genome")
    genome_id = StringField()
    name = StringField()
    assembly = StringField()
    species = StringField()
