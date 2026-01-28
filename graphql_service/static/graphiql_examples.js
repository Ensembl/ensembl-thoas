/**
 * GraphiQL example library for the Ensembl Core (Thoas-style) GraphQL schema.
 *
 * - Beginner-friendly: NO GraphQL variables (all args are literal).
 * - Each example uses a named operation: `query SomeName { ... }`
 * - Grouped by the root Query fields that exist in this schema:
 *   version, gene, genes, transcript, product, overlap_region, region, genomes, genome
 *
 * Notes:
 * - Some examples use known public IDs (BRCA2) and a sample genome UUID from the Ensembl demo.
 * - If a particular ID doesn't exist in your deployment, GraphiQL autocomplete will guide you:
 *   run the "genomes" example first to find a valid genome_id/genome_uuid for your data.
 */

(function () {
  "use strict";

  // Export for the GraphiQL UI code to consume (supports grouped format)
  window.GRAPHIQL_EXAMPLES = [
    {
      section: "genomes",
      items: [
        {
          name: "Genomes by assembly accession",
          description: "Search genomes by assembly accession. Use this to discover genome_id values",
          query: `query GenomesByAssemblyAccession {
  genomes(by_keyword: { 
    assembly_accession_id: "GCA_000001405.29" 
  }) {
    genome_id
    scientific_name
    assembly_accession
    release_date
  }
}`,
        },
        {
          name: "Genomes by common name (bee)",
          description: "Another keyword search to discover genome_id by common_name",
          query: `query GenomesByCommonName {
  genomes(by_keyword: { common_name: "bee" }) {
    genome_id
    scientific_name
    assembly_accession
    release_number
  }
}`,
        },
      ],
    },

    {
      section: "genome",
      items: [
        {
          name: "Genome by ID",
          description: "Fetch a genome using its ID. See 'genomes' section above for an example of how to find a genome ID",
          query: `query GenomeByID {
  genome(by_genome_id: { 
    genome_id: "a7335667-93e7-11ec-a39d-005056b38ce3" 
  }) {
    genome_id
    scientific_name
    assembly_accession
    release_date
    taxon_id
    tol_id
  }
}`,
        },
      ],
    },

    {
      section: "gene",
      items: [
        {
          name: "Gene minimal (stable_id + name)",
          description: "Smallest useful gene query by_id",
          query: `query GeneMinimal {
  gene(by_id: { 
    genome_id: "a7335667-93e7-11ec-a39d-005056b38ce3", 
    stable_id: "ENSG00000139618" 
  }) {
    stable_id
    symbol
    name
    so_term
  }
}`,
        },
        {
          name: "Gene with transcripts (first fields)",
          description: "Traverse from a gene to its transcripts",
          query: `query GeneWithTranscripts {
  gene(by_id: { 
    genome_id: "a7335667-93e7-11ec-a39d-005056b38ce3", 
    stable_id: "ENSG00000139618" 
  }) {
    stable_id
    symbol
    transcripts {
      stable_id
      symbol
      so_term
      version
    }
  }
}`,
        },
        {
          name: "Gene transcripts page (pagination)",
          description: "Paginated transcripts (page/per_page)",
          query: `query GeneTranscriptsPage {
  gene(by_id: { 
    genome_id: "a7335667-93e7-11ec-a39d-005056b38ce3", 
    stable_id: "ENSG00000139618" 
  }) {
    stable_id
    transcripts_page(page: 1, per_page: 5) {
      page_metadata {
        total_count
        page
        per_page
      }
      transcripts {
        stable_id
        symbol
      }
    }
  }
}`,
        },
        {
          name: "Gene external references",
          description: "Show xrefs attached to a gene (accession, name, method, url)",
          query: `query GeneExternalReferences {
  gene(by_id: { 
    genome_id: "a7335667-93e7-11ec-a39d-005056b38ce3", 
    stable_id: "ENSG00000139618" 
  }) {
    stable_id
    symbol
    external_references {
      accession_id
      name
      url
      source {
        name
      }
      assignment_method {
        type
        description
      }
    }
  }
}`,
        },
      ],
    },

    {
      section: "genes",
      items: [
        {
          name: "Genes by symbol (BRCA2)",
          description: "Search genes by symbol + genome_id",
          query: `query GenesBySymbol {
  genes(by_symbol: { 
    genome_id: "a7335667-93e7-11ec-a39d-005056b38ce3", 
    symbol: "BRCA2" 
  }) {
    stable_id
    symbol
    name
    so_term
  }
}`,
        },
      ],
    },

    {
      section: "transcript",
      items: [
        {
          name: "Transcript minimal",
          description: "Fetch a transcript by_id",
          query: `query TranscriptMinimal {
  transcript(by_id: { 
    genome_id: "a7335667-93e7-11ec-a39d-005056b38ce3", 
    stable_id: "ENST00000380152" 
  }) {
    stable_id
    symbol
    so_term
    version
  }
}`,
        },
        {
          name: "Transcript with parent gene",
          description: "Get the parent gene of a transcript",
          query: `query TranscriptWithGene {
  transcript(by_id: { 
    genome_id: "a7335667-93e7-11ec-a39d-005056b38ce3", 
    stable_id: "ENST00000380152" 
  }) {
    stable_id
    symbol
    gene {
      stable_id
      symbol
      name
      so_term
    }
  }
}`,
        },
        {
          name: "Transcript slice + relative location",
          description: "Shows the transcript's slice and its relative location (handy for coordinates)",
          query: `query TranscriptSliceAndLocation {
  transcript(by_id: { 
    genome_id: "a7335667-93e7-11ec-a39d-005056b38ce3", 
    stable_id: "ENST00000380152" 
  }) {
    stable_id
    slice {
      region {
        name
        length
      }
      strand {
        code
        value
      }
      location {
        start
        end
        length
      }
    }
    relative_location {
      start
      end
      length
    }
  }
}`,
        },
      ],
    },

    {
      section: "product (e.g protein)",
      items: [
        {
          name: "Product by_id",
          description: "Fetch a product (protein) by genome_id + product stable_id",
          query: `query ProductById {
  product(by_id: { 
    genome_id: "a7335667-93e7-11ec-a39d-005056b38ce3", 
    stable_id: "ENSP00000369497.3" 
  }) {
    stable_id
    unversioned_stable_id
    version
    length
    type
    sequence {
      checksum
    }
  }
}`,
        },
        {
          name: "Product external references",
          description: "Show xrefs for a product. Replace the product stable_id",
          query: `query ProductExternalReferences {
  product(by_id: { 
    genome_id: "a7335667-93e7-11ec-a39d-005056b38ce3", 
    stable_id: "ENSP00000369497.3" 
  }) {
    stable_id
    external_references {
      accession_id
      name
      assignment_method {
        type
        description
      }
      url
    }
  }
}`,
        },
      ],
    },

    {
      section: "overlap_region",
      items: [
        {
          name: "Overlap region (BRCA2 locus on chr13)",
          description: "Fetch locus overlapping a slice (genes + transcripts)",
          query: `query OverlapRegionBRCA2Locus {
  overlap_region(
    by_slice: {
      genome_id: "a7335667-93e7-11ec-a39d-005056b38ce3"
      region_name: "13"
      start: 32315000
      end: 32405000
    }
  ) {
    genes {
      stable_id
      symbol
      name
      so_term
    }
    transcripts {
      stable_id
      symbol
      so_term
    }
  }
}`,
        },
      ],
    },

    {
      section: "region",
      items: [
        {
          name: "Region by name (chr13)",
          description: "Fetch a region by name. If your region names differ (e.g. 'chr13'), update the name field.",
          query: `query RegionByName {
  region(by_name: { 
    genome_id: "a7335667-93e7-11ec-a39d-005056b38ce3", 
    name: "13" 
  }) {
    name
    length
    code
    topology
    assembly {
      name
      accession_id
      accessioning_body
      default
    }
  }
}`,
        },
        {
          name: "Region sequence checksum (Refget-friendly)",
          description: "Gets the sequence checksum and length (you can get the sequence by providing the checksum to our RefGet API).",
          query: `query RegionSequenceChecksum {
  region(by_name: { 
    genome_id: "a7335667-93e7-11ec-a39d-005056b38ce3", 
    name: "13" 
  }) {
    code
    name
    length
    sequence {
      checksum
    }
  }
}`,
        },
      ],
    },

    {
      section: "multi-query (aliases)",
      items: [
        {
          name: "Gene + Transcript in one request",
          description: "Demonstrates aliases and fetching multiple roots without variables.",
          query: `query GeneAndTranscript {
  gene: gene(by_id: { 
    genome_id: "a7335667-93e7-11ec-a39d-005056b38ce3", 
    stable_id: "ENSG00000139618" 
  }) {
    stable_id
    symbol
    name
  }
  tx: transcript(by_id: { 
    genome_id: "a7335667-93e7-11ec-a39d-005056b38ce3", 
    stable_id: "ENST00000380152" 
  }) {
    stable_id
    symbol
    so_term
  }
}`,
        },
        {
          name: "Discover root Query fields (introspection)",
          description: "Lists the top-level query operations available on this endpoint.",
          query: `query ListRootQueryFields {
  __schema {
    queryType {
      fields {
        name
        description
      }
    }
  }
}`,
        },
      ],
    },
  ];
})();
