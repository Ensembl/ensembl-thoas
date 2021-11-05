'''
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
'''

import argparse
import asyncio
import asyncio.subprocess
import configparser
import os

async def run_assembly(args):
    '''
    Successively run each of the three scripts
    '''
    code = os.path.dirname(os.path.realpath(__file__))
    # Append the correct release number, division, and override the base path for GRCh37
    if args['assembly'] == 'GRCh37':
        data = '/nfs/nobackup/ensembl/kamal/search-dump/thoas/vertebrates/json/'
    else:
        data = f'{args["base_data_path"]}/release-{args["release"]}/{args["division"]}/json/'

    collection_param = '' if not args["collection"] else f'--collection {args["collection"]}'

    shell_command = f'''
        perl {code}/extract_cds_from_ens.pl --host={args["host"]} --user={args["user"]} --port={args["port"]} --species={args["production_name"]} --assembly={args["assembly"]};\
        python {code}/load_proteins.py --section_name {args["section_name"]} --config_file {args["config_file"]};\
        python {code}/load_genome.py --data_path {data} --species {args["production_name"]} --config_file {args["config_file"]} {collection_param} --assembly={args["assembly"]} --release={args["release"]};\
        python {code}/load_genes.py --data_path {data} --classifier_path {args["classifier_path"]} --species {args["production_name"]} --config_file {args["config_file"]} {collection_param} --assembly={args["assembly"]} --release={args["release"]};\
        python {code}/dump_proteins.py --section_name {args["section_name"]} --config_file {args["config_file"]}
    '''
    await asyncio.create_subprocess_shell(shell_command)


if __name__ == '__main__':

    ARG_PARSER = argparse.ArgumentParser()
    ARG_PARSER.add_argument(
        '--config',
        help='Config file containing the database and division info for species and MongoDB',
        default='load.conf'
    )
    ARG_PARSER.add_argument(
        '--base_data_path',
        help='Path to data dumps, e.g. /hps/nobackup2/production/ensembl/ensprod/search_dumps'
    )
    ARG_PARSER.add_argument(
        '--classifier_path',
        help='Path to JSON files for the gene/transcript metadata classifiers'
    )
    ARG_PARSER.add_argument(
        '--release',
        help='Ensembl release number, 100'
    )
    CONF_PARSER = configparser.ConfigParser()

    CLI_ARGS = ARG_PARSER.parse_args()
    CONF_PARSER.read(CLI_ARGS.config)
    print('Dumping data to {} and loading to MongoDB'.format(os.getcwd()))

    # each section of the file dictates a particular assembly to work on
    for section in CONF_PARSER.sections():
        # one section is MongoDB config, the rest are species info
        if section in ['MONGO DB', 'REFGET DB', 'GENERAL']:
            continue

        # Get extra parameters from the GENERAL section.
        # The per-section parameters will override any GENERAL ones if there is a collision.
        section_args = {**CONF_PARSER['GENERAL'], **CONF_PARSER[section]}
        section_args['config_file'] = CLI_ARGS.config
        section_args['section_name'] = section
        asyncio.run(run_assembly(args=section_args))
