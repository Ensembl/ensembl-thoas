# Use of Identifiers.org API to generate Xref URLs

URLs to external resources should be generated dynamically. Otherwise archive
data will gradually go stale and links will fail to resolve. GraphQL middleware
presents an opportunity to convert serialised data into URLs before returning
to the client.

This might work by making the GraphQL service pull in the latest identifier
information on start-up. Pretty-printed JSON only occupies 1.8 MB, so the
memory cost should be reasonably small, however service restarts and worker
churn will tend to create bursts of requests for the same information. Ideally
it should be fetched before pre-forking.

Otherwise we could inject the data into containers to be read on demand to
desynchronise our service start-up from indentifiers.org data requests.

## Requesting data from identifiers.org

The URI resolution service offers several forms of interaction:

1. Whole data dump as JSON via https://registry.api.identifiers.org/resolutionApi/getResolverDataset
2. Individual requests via Namespace, Resource, Institution, and Location

I think it better to cache the whole lot rather than introducing latency when
resolving individual links (possibly in the hundreds per page view)

## Potential issues

1. Identifiers.org is unavailable at service start
2. Identifiers.org is retired
3. Linking Ensembl internal external_db entities to Identifiers.org namespaces

## Bonuses for working this way

1. Externalise URL generation and maintenance
2. EBI service interaction and sharing


## A document trimmed down to Uniprot from the API
```
{
  "id": 23,
  "prefix": "uniprot",
  "mirId": "MIR:00000005",
  "name": "UniProt Knowledgebase",
  "pattern": "^([A-N,R-Z][0-9]([A-Z][A-Z, 0-9][A-Z, 0-9][0-9]){1,2})|([O,P,Q][0-9][A-Z, 0-9][A-Z, 0-9][A-Z, 0-9][0-9])(\\.\\d+)?$",
  "description": "The UniProt Knowledgebase (UniProtKB) is a comprehensive resource for protein sequence and functional information with extensive cross-references to more than 120 external databases. Besides amino acid sequence and a description, it also provides taxonomic data and citation information.",
  "created": "2019-06-11T14:15:29.457+0000",
  "modified": "2019-06-11T14:15:29.457+0000",
  "resources": [
    {
      "id": 25,
      "mirId": "MIR:00100164",
      "urlPattern": "https://purl.uniprot.org/uniprot/{$id}",
      "name": "Universal Protein Resource using Persistent URL system",
      "description": "Universal Protein Resource using Persistent URL system",
      "official": true,
      "providerCode": "CURATOR_REVIEW",
      "sampleId": "P0DP23",
      "resourceHomeUrl": "https://www.uniprot.org/",
      "institution": {
        "id": 24,
        "name": "UniProt Consortium",
        "homeUrl": "CURATOR_REVIEW",
        "description": "CURATOR_REVIEW",
        "rorId": null,
        "location": {
          "countryCode": "GB",
          "countryName": "United Kingdom"
        }
      },
      "location": {
        "countryCode": "GB",
        "countryName": "United Kingdom"
      },
      "deprecated": false,
      "deprecationDate": null
    },
    {
      "id": 27,
      "mirId": "MIR:00100330",
      "urlPattern": "https://www.ncbi.nlm.nih.gov/protein/{$id}",
      "name": "UniProt through NCBI",
      "description": "UniProt through NCBI",
      "official": false,
      "providerCode": "ncbi",
      "sampleId": "P0DP23",
      "resourceHomeUrl": "https://www.ncbi.nlm.nih.gov/protein/",
      "institution": {
        "id": 26,
        "name": "National Center for Biotechnology Information (NCBI)",
        "homeUrl": "CURATOR_REVIEW",
        "description": "CURATOR_REVIEW",
        "rorId": null,
        "location": {
            "countryCode": "US",
            "countryName": "United States"
        }
      },
      "location": {
          "countryCode": "US",
          "countryName": "United States"
      },
      "deprecated": false,
      "deprecationDate": null
    }
  ],
  "sampleId": "P0DP23",
  "namespaceEmbeddedInLui": false,
  "deprecated": false,
  "deprecationDate": null
}
```

The document shows how we can extract homepage for a resource, as well as a URL
pattern required to prefix an ID in order to resolve the record