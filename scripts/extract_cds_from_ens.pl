# Perl script to extract Transcript IDs and their CDS start and end
# coords w.r.t. Transcript coordinates, i.e. CDS_start = 1 (not a big number)

use strict;
use warnings;
use Bio::EnsEMBL::Registry;
use IO::File;
use List::Util 'sum';
use Getopt::Long;
use Pod::Usage;

my $registry = 'Bio::EnsEMBL::Registry';

my $species = 'homo_sapiens'; # Needs to be a production name
my $host = 'ensembldb.ensembl.org'; # Very slow!
my $user = 'anonymous';
my $port = 3306;
my $help;

GetOptions(
  "species=s" => \$species,
  "host=s" => \$host,
  "user=s" => \$user,
  "port=i" => \$port,
  "h|?" => \$help
);


die 'Specify a species production name at command line' unless $species;
$registry->load_registry_from_db(
  -host => $host,
  -user => $user,
  -species => $species,
  -port => $port
);

my $fh = IO::File->new($species. '.csv', 'w');
print $fh '"transcript ID", "cds_start", "cds_end", "cds relative start",'.
  '"cds relative end", "spliced_length"'."\n";

my $transcript_adaptor = $registry->get_adaptor($species, 'core', 'Transcript');


my $transcripts = $transcript_adaptor->fetch_all;
my $x = 0;
while (my $transcript = shift @$transcripts) {
  $x++;
  my $translation = $transcript->translation;
  next unless $translation;
  my $start = $translation->start;
  my $end = $translation->end;
  my $start_exon = $translation->start_Exon;
  my $end_exon = $translation->end_Exon;

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

}
print "Dumping completed of $x of coding transcripts\n";