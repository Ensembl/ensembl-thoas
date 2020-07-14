# Perl script to extract Transcript IDs and their CDS start and end
# coords w.r.t. Transcript coordinates, i.e. CDS_start = 1 (not a big number)
# Dumps a second file containing phase information on a per transcript basis

use strict;
use warnings;
use Bio::EnsEMBL::Registry;
use IO::File;
use List::Util 'sum';
use Getopt::Long;
use Pod::Usage;
use Bio::EnsEMBL::ApiVersion 'software_version';
use Bio::EnsEMBL::MetaData::DBSQL::MetaDataDBAdaptor;
use Bio::EnsEMBL::LookUp::RemoteLookUp;

my $registry = 'Bio::EnsEMBL::Registry';

my $species = 'homo_sapiens'; # Needs to be a production name
my $assembly; # Required to differentiate between assemblies of the same species
my $host = 'ensembldb.ensembl.org'; # Very slow!
my $user = 'anonymous';
my $port = 3306;
my $meta_host = 'mysql-ens-meta-prod-1.ebi.ac.uk';
my $meta_port = 4483;
my $meta_dbname = 'ensembl_metadata';
my $meta_user = 'ensro';
my $help;
# Set Ensembl/EnsemblGenomes release version.
# Needed for bacteria/fungi (for collection databases)
my $ENS_VERSION = software_version();
my $EG_VERSION = software_version() - 53;

GetOptions(
  "species=s" => \$species,
  "assembly=s" => \$assembly,
  "host=s" => \$host,
  "user=s" => \$user,
  "port=i" => \$port,
  "meta_host=s" => \$meta_host,
  "meta_port=i" => \$meta_port,
  "meta_dbname=s" => \$meta_dbname,
  "meta_user=s" => \$meta_user,
  "h|?" => \$help
);


die 'Specify a species production name and assembly at command line' unless $species && $assembly;

my $fh = IO::File->new($species.'_'.$assembly.'.csv', 'w');
print $fh '"transcript ID", "cds_start", "cds_end", "cds relative start",'.
  '"cds relative end", "spliced_length"'."\n";
# Time to run a second file relating to phase of each exon in each transcript
# Don't want to jam it into a single line of the CDS file
my $phase_fh = IO::File->new($species.'_'.$assembly.'_phase.csv', 'w');
print $phase_fh '"transcript ID","exon ID","rank","start_phase","end_phase"'."\n";

my $transcript_adaptor;
if ($host =~ /mysql-ens-mirror-[3,4]/) {
  my $metadata_dba = Bio::EnsEMBL::MetaData::DBSQL::MetaDataDBAdaptor->new(
                       -USER => $meta_user,
                       -DBNAME => $meta_dbname,
                       -HOST => $meta_host,
                       -PORT => $meta_port);
  my $gdba = $metadata_dba->get_GenomeInfoAdaptor($EG_VERSION);

  $gdba->set_ensembl_genomes_release($EG_VERSION);
  $gdba->set_ensembl_release($ENS_VERSION);
  # Database host, port, user needs to be changed based on where the data is for species/division
  my $lookup = Bio::EnsEMBL::LookUp::RemoteLookUp->new(
    -user => $user,
    -port => $port,
    -host => $host,
    -adaptor=>$gdba
  );
  my $dbas = $lookup->get_by_name_exact($species);
  $transcript_adaptor = ${ $dbas }[0]->get_adaptor("Transcript");
} else {
  $registry->load_registry_from_db(
    -host => $host,
    -user => $user,
    -species => $species,
    -port => $port
  );
  $transcript_adaptor = $registry->get_adaptor($species, 'core', 'Transcript');
}

my $transcripts = $transcript_adaptor->fetch_all;
my $x = 0;
while (my $transcript = shift @$transcripts) {
  $x++;
  my $translation = $transcript->translation;
  next unless $translation;
  my $start = $translation->start;
  my $end = $translation->end;

  my $transcript_slice = $transcript->feature_Slice;
  my $cds_feats = $transcript->get_all_CDS();
  # Note that CDS coords in transcript space are 5' to 3', so always
  # are ascending. We don't care about the intervening CDSes for 
  # rendering purposes.

  if (@$cds_feats > 1) {
    my ($relative_first_cds) = $cds_feats->[0]->transfer($transcript_slice);
    my ($relative_last_cds) = $cds_feats->[-1]->transfer($transcript_slice);
    printf $fh "%s,%s,%s,%s,%s,%s\n",
      $transcript->stable_id,
      $cds_feats->[0]->start,
      $cds_feats->[-1]->end,
      $relative_first_cds->start,
      $relative_last_cds->end,
      sum map {$_->length} @$cds_feats;
  } else {
    my ($relative_cds) = $cds_feats->[0]->transfer($transcript_slice);
    printf $fh "%s,%s,%s,%s,%s,%s\n",
      $transcript->stable_id,
      $cds_feats->[0]->start,
      $cds_feats->[0]->end,
      $relative_cds->start,
      $relative_cds->end,
      $cds_feats->[0]->length;
  }

  foreach my $et (@{$transcript->get_all_ExonTranscripts}) {
    my $exon = $et->exon;
    printf $phase_fh "%s,%s,%s,%s,%s\n",
      $transcript->stable_id,
      $exon->stable_id,
      $et->rank,
      $exon->phase,
      $exon->end_phase;
  }
}
print "Dumping completed of $x of coding transcripts\n";

close $fh;
close $phase_fh;
