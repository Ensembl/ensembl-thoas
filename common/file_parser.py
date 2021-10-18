class ChromosomeChecksum:
    def __init__(self, genome_id):
        self.genome_id = genome_id
        self.flat_file = "/nfs/services/enswbsites/newsite/data/chromosome_checksums/" + self.genome_id + "/chrom.hashes"
        self.results_dict = {}
        try:
            with open(self.flat_file) as chrom_hashes_file:
                for line in chrom_hashes_file:
                    chr_id, md5, *_ = line.split()
                    self.results_dict[chr_id] = md5
        except FileNotFoundError:
            raise FileNotFoundError(self.flat_file + " Not Found")

    def get_checksum(self, chromosome_id):
        return self.results_dict.get(chromosome_id, None)



