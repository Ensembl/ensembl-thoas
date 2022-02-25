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
import subprocess
from datetime import datetime


def get_repo_path():
    return os.path.dirname(os.path.realpath(__file__))


def get_default_collection_name():
    '''Creates a default mongo collection name of the form graphql_<timestamp>_<git hash>,
    eg graphql_211129152013_876a48b'''
    cwd = os.getcwd()
    repo_path = get_repo_path()
    os.chdir(repo_path)
    current_commit_git_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    os.chdir(cwd)
    current_time = datetime.now().strftime("%y%m%d%H%M%S")
    return "_".join(["graphql", current_time, current_commit_git_hash])


async def run_assembly(args):
    '''
    Successively run all the other loading scripts
    '''
    code = get_repo_path()
    # Append the correct release number, division, and override the base path for GRCh37
    if args['assembly'] == 'GRCh37':
        data = '/nfs/nobackup/ensembl/kamal/search-dump/thoas/vertebrates/json/'
    else:
        data = f'{args["base_data_path"]}/release-{args["release"]}/{args["division"]}/json/'

    collection_param = '' if 'collection' not in args else f'--collection {args["collection"]}'

    log_faulty_urls = '--log_faulty_urls' if 'log_faulty_urls' in args and args['log_faulty_urls'] == 'True' else ''

    mongo_collection_name = get_default_collection_name()

    shell_command = f'''
        perl {code}/extract_cds_from_ens.pl --host={args["host"]} --user={args["user"]} --port={args["port"]} --species={args["production_name"]} --assembly={args["assembly"]};\
        python {code}/prepare_gene_name_metadata.py --section_name {args["section_name"]} --config_file {args["config_file"]};\
        python {code}/dump_proteins.py --section_name {args["section_name"]} --config_file {args["config_file"]};\
        python {code}/load_genome.py --data_path {data} --species {args["production_name"]} --config_file {args["config_file"]} {collection_param} --assembly={args["assembly"]} --release={args["release"]} --mongo_collection={mongo_collection_name};\
        python {code}/load_genes.py --data_path {data} --classifier_path {args["classifier_path"]} --species {args["production_name"]} --config_file {args["config_file"]} {collection_param} --assembly={args["assembly"]} --xref_lod_mapping_file={args["xref_lod_mapping_file"]} --release={args["release"]} --mongo_collection={mongo_collection_name} {log_faulty_urls};\
        python {code}/load_regions.py --section_name {args["section_name"]} --config_file {args["config_file"]} --chr_checksums_path {args["chr_checksums_path"]}  --mongo_collection={mongo_collection_name}
    '''
    await asyncio.create_subprocess_shell(shell_command)


if __name__ == '__main__':

    ARG_PARSER = argparse.ArgumentParser()
    ARG_PARSER.add_argument(
        '--config',
        help='Config file containing the database and division info for species and MongoDB',
        default='load.conf'
    )
    CONF_PARSER = configparser.ConfigParser()

    CLI_ARGS = ARG_PARSER.parse_args()
    CONF_PARSER.read(CLI_ARGS.config)
    print(f'Dumping data to {os.getcwd()} and loading to MongoDB')

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
