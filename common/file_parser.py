import os

class ChromosomeChecksum:
    def __init__(self, genome_id, chr_checksums_path):
        self.genome_id = genome_id
        self.flat_file = os.path.join(chr_checksums_path, self.genome_id, "chrom.hashes")
        self.results_dict = {}
        with open(self.flat_file) as chrom_hashes_file:
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
