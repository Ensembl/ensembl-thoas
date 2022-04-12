import http from 'k6/http';
import { check, sleep } from 'k6';
import jsonpath from "https://jslib.k6.io/jsonpath/1.0.2/index.js";

/*
export default function () {
  const url = 'http://2020.ensembl.org/api/thoas';
  const payload = JSON.stringify({
    operationName: null,
    variables: {},
    query: "gene(byId: {genome_id: \"saccharomyces_cerevisiae_GCA_000146045_2\", stable_id: \"YDL168W\"}) {\n    stable_id\n    transcripts {\n      stable_id\n    }\n  }\n}\n"
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const res = http.post(url, payload, params);
  check(res, { 'status was 200': (r) => r.status == 200 });
}
*/

export const options = {
  vus: 2,
  duration: '5s',
};

export default function main() {
  let response;
  // Thoas URL 
  const url = 'http://localhost:8000/thoas';

  response = http.post(
    url,
    '{\n  "query": "\\n  query TrackPanelGene {\\n    gene(byId: { genome_id: \\"homo_sapiens_GCA_000001405_28\\", stable_id: \\"ENSG00000139618\\" }) {\\n      stable_id\\n      unversioned_stable_id\\n      symbol\\n      slice {\\n        region {\\n          name\\n        }\\n        location {\\n          start\\n          end\\n        }\\n        strand {\\n          code\\n        }\\n      }\\n      metadata {\\n        biotype {\\n          label\\n        }\\n      }\\n      transcripts {\\n        stable_id\\n        slice {\\n          location {\\n            length\\n          }\\n        }\\n        product_generating_contexts {\\n          product_type\\n        }\\n        metadata {\\n          biotype {\\n            label\\n          }\\n          canonical {\\n            value\\n            label\\n          }\\n          mane {\\n            value\\n            label\\n            ncbi_transcript {\\n              id\\n              url\\n            }\\n          }\\n        }\\n      }\\n    }\\n  }\\n",\n  "variables": {}\n}\n',
    {
      headers: {
        "Content-Type": "application/json",
      },
    }
  );
  check(response, {
    "status equals 200": response => response.status.toString() === "200",
    "$.data.gene.stable_id is ENSG00000139618.17": response =>
      jsonpath
        .query(response.json(), "$.data.gene.stable_id")
        .some(value => value === "ENSG00000139618.17"),
    "$.data.gene.slice.region.name is 13": response =>
      jsonpath
        .query(response.json(), "$.data.gene.slice.region.name")
        .some(value => value === "13"),
  });

  // Automatically added sleep
  sleep(1);
}
