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

import os

class ChromosomeChecksum:
    def __init__(self, genome_id, chr_checksums_path):
        self.genome_id = genome_id
        self.flat_file = os.path.join(chr_checksums_path, self.genome_id, "chrom.hashes")
        self.results_dict = {}
        with open(self.flat_file, encoding='UTF-8') as chrom_hashes_file:
            for line in chrom_hashes_file:
                chr_id, md5, *_ = line.split()
                self.results_dict[chr_id] = md5

    def get_checksum(self, chromosome_id):
        return self.results_dict.get(chromosome_id, None)


class MockChromosomeChecksum:

    def __init__(self, genome_id, chr_checksums_path):
        self.genome_id = genome_id
        self.flat_file = chr_checksums_path

    def get_checksum(self, chromosome_id):
        return '3t6fit96jy015frnh465do005hd885jtki'
