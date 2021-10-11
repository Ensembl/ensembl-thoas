
class ChromosomeChecksum:
    def __init__(self, genome_id):
        self.genome_id = genome_id
        self.flat_file = "/nfs/services/enswbsites/newsite/staging/genome_browser/4/common_files/" + self.genome_id + "/chrom.hashes"
        self.results_dict = {}
        file = open(self.flat_file)
        for line in file:
            chr_id, md5, *_ = line.split()
            self.results_dict[chr_id] = md5

    def get_checksum(self, chromosome_id):
        return self.results_dict.get(chromosome_id, None)



