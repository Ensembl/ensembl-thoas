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

from configparser import ConfigParser
import argparse


def load_config(filename):
    'Load a config, return a ConfigParser object'

    cp = ConfigParser(default_section='MONGO DB')
    cp.read(filename)
    return cp


def parse_args():
    '''
    Common parameter parsing for data loading scripts
    '''
    parser = argparse.ArgumentParser(
        description='Load JSON Search dumps into MongoDB for GraphQL'
    )
    parser.add_argument(
        '--config_file',
        help='File path containing MongoDB credentials',
        default='../mongo.conf'
    )
    parser.add_argument(
        '--data_path',
        help='Path to JSON files from the "Gene search" dumps',
        default='/hps/nobackup2/production/ensembl/ensprod/search_dumps/release-99/vertebrates/json/'
    )
    parser.add_argument(
        '--species',
        help='The production name for a (sic) Ensembl species',
        default='homo_sapiens'
    )
    return parser.parse_args()
