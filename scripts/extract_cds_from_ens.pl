# Perl script to extract Transcript IDs and their CDS start and end
# coords w.r.t. Transcript coordinates, i.e. CDS_start = 1 (not a big number)

use strict;
use warnings;
use Bio::EnsEMBL::Registry;
use IO::File;

my $registry = 'Bio::EnsEMBL::Registry';

my $species = shift;
die 'Specify a species production name at command line' unless $species;
$registry->load_registry_from_db(
  -host => 'ensembldb.ensembl.org',
  -user => 'anonymous',
  -species => $species
);

my $fh = IO::File->new($species. '.csv', 'w');
print $fh '"transcript ID", "cds start", "cds end"'."\n";

my $transcript_adaptor = $registry->get_adaptor('human', 'core', 'Transcript');


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
    my ($start_seg) = $cds_feats->[0]->transfer($transcript_slice);
    my ($end_seg) = $cds_feats->[-1]->transfer($transcript_slice);
    printf $fh "%s,%s,%s\n", $transcript->stable_id, $start_seg->start, $end_seg->end;
  } else {
    my ($seg) = $cds_feats->[0]->transfer($transcript_slice);
    printf $fh "%s,%s,%s\n", $transcript->stable_id, $seg->start, $seg->end;
  }

}
print "Dumping completed";