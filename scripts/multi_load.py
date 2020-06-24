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

import asyncio
import asyncio.subprocess
import os
from common.utils import wrapper_parse_args

# python load_genes.py --config_file mongo.conf --data_path /hps/nobackup2/production/ensembl/ensprod/search_dumps/release-100/protists/json/ --species plasmodium_falciparum --assembly ASM276v2
# python scripts/load_genome.py --config_file scripts/mongo.conf --data_path /hps/nobackup2/production/ensembl/ensprod/search_dumps/release-100/protists/json/ --species  plasmodium_falciparum
# saccharomyces_cerevisiae  R64-1-1
# homo_sapiens  GRCh38
# caenorhabditis_elegans  WBcel235
# plasmodium_falciparum  ASM276v2
# triticum_aestivum  IWGSC
# escherichia_coli_str_k_12_substr_mg1655 ASM584v2

ASSEMBLIES = (
    ('homo_sapiens', 'GRCh38', 'vertebrates'),
    ('homo_sapiens', 'GRCh37', 'vertebrates'),
    ('saccharomyces_cerevisiae', 'R64-1-1', 'vertebrates'),
    ('caenorhabditis_elegans', 'WBcel235', 'vertebrates'),
    ('plasmodium_falciaparum', 'ASM276v2', 'protists'),
    ('triticum_aestivum', 'IWGSC', 'plants'),
    ('escherichia_coli_str_k_12_substr_mg1655', 'ASM584v2', 'bacteria')
)

async def run_assembly(production_name, assembly, division, args):
    '''
    Successively run each of the three scripts
    '''
    code = os.path.dirname(os.path.realpath(__file__))
    if assembly == 'GRCh37':
        data = '/nfs/nobackup/ensembl/kamal/search-dump/thoas/vertebrates/json/homo_sapiens'
    else:
        data = f'{args.base_data_path}/{args.release}/{division}/json/'
    await asyncio.create_subprocess_shell(
        f'''
        perl {code}/extract_cds_from_ens.pl --host={args.host} --user={args.user} --port={args.port} --species={production_name};\
        python {code}/scripts/load_genome.py --data_path {data} --species{production_name} --config_file {args.config_file};\
        python {code}/scripts/load_genes.py --data_path {data} --species{production_name} --config_file {args.config_file}
        ''',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )


if __name__ == '__main__':

    ARGS = wrapper_parse_args()

    print('Dumping data to %s', os.getcwd())

    for settings in ASSEMBLIES:
        asyncio.run(run_assembly(*settings, ARGS))
